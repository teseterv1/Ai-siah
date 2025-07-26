import os  
os.environ['KIVY_METRICS_DENSITY'] = '1'  
os.environ['KIVY_WINDOW'] = 'sdl2'  
  
from kivy.app import App  
from kivy.lang import Builder  
from kivy.properties import ListProperty, StringProperty, BooleanProperty  
from kivy.uix.boxlayout import BoxLayout  
from kivy.uix.widget import Widget  
from kivy.metrics import dp, sp  
from kivy.clock import Clock  
from kivy.core.window import Window  
from threading import Thread  
from datetime import datetime  
import traceback  

from openai import OpenAI  
  
# Your OpenAI API key here (private, replace before running)  
OPENAI_API_KEY = ""  
client = OpenAI(api_key=OPENAI_API_KEY)  
  
KV = '''  
<ChatBubble@BoxLayout>:  
    text: ''  
    timestamp: ''  
    bg_color: 0, 0, 0, 1  
    text_color: 1, 1, 1, 1  
    size_hint_y: None  
    padding: dp(30)  
    orientation: 'vertical'  
    height: self.minimum_height  
    canvas.before:  
        Color:  
            rgba: root.bg_color  
        RoundedRectangle:  
            pos: self.pos  
            size: self.size  
            radius: [20]  
  
    Label:  
        text: root.text  
        font_size: '48sp'  
        size_hint_y: None  
        height: self.texture_size[1] + dp(60)  
        text_size: self.width - dp(60), None  
        color: root.text_color  
        halign: 'left'  
        valign: 'middle'  
  
    Label:  
        text: root.timestamp  
        font_size: '20sp'  
        color: [0.6, 0.6, 0.6, 1]  
        size_hint_y: None  
        height: dp(30)  
        halign: 'right'  
        valign: 'middle'  
        text_size: self.width, None  
  
<ChatScreen>:  
    orientation: 'vertical'  
    bg_color: root.bg_color  
    canvas.before:  
        Color:  
            rgba: root.bg_color  
        Rectangle:  
            pos: self.pos  
            size: self.size  
  
    BoxLayout:  
        size_hint_y: None  
        height: dp(150)  
        padding: dp(30)  
        spacing: dp(30)  
        Widget:  
        Label:  
            text: "Siah_ai"  
            font_size: '72sp'  
            bold: True  
            color: root.text_color  
        Button:  
            text: '🌙' if not root.is_dark else '☀️'  
            size_hint_x: None  
            width: dp(120)  
            font_size: '48sp'  
            on_release: root.toggle_theme()  
            background_normal: ''  
            background_color: root.button_bg_color  
            color: root.button_text_color  
        Widget:  
  
    ScrollView:  
        id: scroll_view  
        do_scroll_x: False  
        do_scroll_y: True  
        GridLayout:  
            id: messages_box  
            cols: 1  
            size_hint_y: None  
            height: self.minimum_height  
            spacing: dp(15)  
            padding: dp(30)  
  
    BoxLayout:  
        size_hint_y: None  
        height: dp(195)  
        spacing: dp(30)  
        padding: dp(30)  
  
        TextInput:  
            id: user_input  
            multiline: False  
            font_size: sp(48)  
            hint_text: "Type a message..."  
            foreground_color: root.text_color  
            background_color: root.input_bg_color  
            on_text_validate: root.send_message()  
            write_tab: False  
            auto_indent: False  
            cursor_color: root.cursor_color  
            disabled: False  
  
        Button:  
            id: send_btn  
            text: "Send"  
            font_size: '48sp'  
            size_hint_x: None  
            width: dp(240)  
            on_release: root.send_message()  
            background_normal: ''  
            background_color: root.button_bg_color  
            color: root.button_text_color  
            disabled: True  
'''  
  
class ChatBubble(BoxLayout):  
    text = StringProperty('')  
    timestamp = StringProperty('')  
    bg_color = ListProperty([0, 0, 0, 1])  
    text_color = ListProperty([1, 1, 1, 1])  
  
class ChatScreen(BoxLayout):  
    is_dark = BooleanProperty(False)  
    bg_color = ListProperty([1, 1, 1, 1])  
    text_color = ListProperty([0, 0, 0, 1])  
    button_text_color = ListProperty([0, 0, 0, 1])  
    button_bg_color = ListProperty([0.9, 0.9, 0.9, 1])  
    input_bg_color = ListProperty([1, 1, 1, 1])  
    cursor_color = ListProperty([0, 0, 0, 1])  
  
    def __init__(self, **kwargs):  
        super().__init__(**kwargs)  
        self.MAX_TEXT_LENGTH = 500  
        self.set_theme_colors()  
        self.chat_history = []  
        self.thinking_bubble = None  
        self.thinking_container = None  
        self._dot_event = None  
        Clock.schedule_once(self.focus_input, 0.5)  
        Clock.schedule_once(lambda dt: self.adjust_font_size(), 0.5)  
        Window.bind(on_resize=lambda *_: self.adjust_font_size())  
        Clock.schedule_once(self.post_init)  
  
    def post_init(self, dt):  
        self.ids.user_input.bind(text=self.on_user_input_text)  
        self.ids.user_input.bind(text=self.limit_text_length)  
        self.update_send_button_state()  
  
    def limit_text_length(self, instance, value):  
        if len(value) > self.MAX_TEXT_LENGTH:  
            instance.text = value[:self.MAX_TEXT_LENGTH]  
  
    def focus_input(self, *args):  
        self.ids.user_input.focus = True  
  
    def set_theme_colors(self):  
        if self.is_dark:  
            self.bg_color = [0.1, 0.1, 0.1, 1]  
            self.text_color = [1, 1, 1, 1]  
            self.button_text_color = [1, 1, 1, 1]  
            self.button_bg_color = [0.3, 0.3, 0.3, 1]  
            self.input_bg_color = [0.2, 0.2, 0.2, 1]  
            self.cursor_color = [1, 1, 1, 1]  
        else:  
            self.bg_color = [1, 1, 1, 1]  
            self.text_color = [0, 0, 0, 1]  
            self.button_text_color = [0, 0, 0, 1]  
            self.button_bg_color = [0.9, 0.9, 0.9, 1]  
            self.input_bg_color = [1, 1, 1, 1]  
            self.cursor_color = [0, 0, 0, 1]  
  
    def toggle_theme(self):  
        self.is_dark = not self.is_dark  
        self.set_theme_colors()  
        self.update_existing_bubbles_colors()  
  
    def update_existing_bubbles_colors(self):  
        for container in self.ids.messages_box.children:  
            for child in container.children:  
                if isinstance(child, ChatBubble):  
                    if child.bg_color == [0.3, 0.6, 1, 1]:  
                        child.text_color = [1, 1, 1, 1]  
                        child.bg_color = [0.2, 0.4, 0.8, 1] if self.is_dark else [0.3, 0.6, 1, 1]  
                    else:  
                        child.text_color = [1, 1, 1, 1] if self.is_dark else [0, 0, 0, 1]  
                        child.bg_color = [0.3, 0.7, 0.3, 1] if self.is_dark else [0.4, 0.9, 0.4, 1]  
  
    def adjust_font_size(self):  
        width = Window.width  
        if width < 800:  
            self.ids.user_input.font_size = sp(32)  
        elif width < 1200:  
            self.ids.user_input.font_size = sp(40)  
        else:  
            self.ids.user_input.font_size = sp(48)  
  
    def on_user_input_text(self, instance, value):  
        self.update_send_button_state()  
  
    def update_send_button_state(self):  
        text = self.ids.user_input.text.strip()  
        self.ids.send_btn.disabled = (not text) or self.ids.user_input.disabled  
  
    def send_message(self):  
        if self.ids.send_btn.disabled:  
            return  
  
        text = self.ids.user_input.text.strip()  
        if not text:  
            return  
  
        self.add_message(text, is_user=True)  
        self.ids.user_input.text = ''  
        self.ids.user_input.focus = True  
  
        self.ids.send_btn.disabled = True  
        self.ids.user_input.disabled = True  
  
        self.show_thinking_bubble()  
  
        def get_ai_response():  
            try:  
                response = client.chat.completions.create(  
                    model="gpt-3.5-turbo",  
                    messages=[  
                        {"role": "system", "content": "You are a helpful assistant."},  
                        {"role": "user", "content": text},  
                    ],  
                    max_tokens=512,  
                    temperature=0.7,  
                )  
                reply = response.choices[0].message.content.strip()  
                if not reply:  
                    reply = "⚠️ Received empty response."  
            except Exception as e:  
                traceback.print_exc()  
                reply = f"⚠️ Error: {str(e)}"  
            Clock.schedule_once(lambda dt: self.update_ai_response(reply), 0)  
  
        Thread(target=get_ai_response, daemon=True).start()  
  
    def show_thinking_bubble(self):  
        self.thinking_bubble = ChatBubble(  
            text="🤖 Thinking",  
            timestamp=datetime.now().strftime("%H:%M"),  
            bg_color=[0.4, 0.9, 0.4, 1],  
            text_color=[0, 0, 0, 1],  
            size_hint_x=0.7  
        )  
        self.thinking_container = BoxLayout(orientation='horizontal', size_hint_y=None, size_hint_x=0.7, padding=[dp(15), 0, dp(15), 0])  
        self.thinking_bubble.bind(height=lambda instance, value: setattr(self.thinking_container, 'height', value + dp(30)))  
  
        self.thinking_container.add_widget(self.thinking_bubble)  
        self.thinking_container.add_widget(Widget())  
        self.ids.messages_box.add_widget(self.thinking_container)  
        Clock.schedule_once(lambda dt: self.scroll_to_bottom(), 0.1)  
  
        dot_cycle = ["🤖 Thinking", "🤖 Thinking.", "🤖 Thinking..", "🤖 Thinking..."]  
        self.dot_index = 0  
  
        def next_dot(*_):  
            if self.thinking_bubble:  
                self.thinking_bubble.text = dot_cycle[self.dot_index % len(dot_cycle)]  
                self.dot_index += 1  
                return True  
            return False  
  
        if self._dot_event:  
            Clock.unschedule(self._dot_event)  
        self._dot_event = Clock.schedule_interval(next_dot, 0.5)  
  
    def update_ai_response(self, response):  
        if self._dot_event:  
            Clock.unschedule(self._dot_event)  
            self._dot_event = None  
  
        if self.thinking_container:  
            self.ids.messages_box.remove_widget(self.thinking_container)  
            self.thinking_container = None  
            self.thinking_bubble = None  
  
        self.add_message(response, is_user=False)  
  
        Clock.schedule_once(lambda dt: self.enable_input(), 0.3)  
  
    def enable_input(self):  
        self.ids.user_input.disabled = False  
        self.update_send_button_state()  
        self.ids.user_input.focus = True  
        self.scroll_to_bottom()  
  
    def add_message(self, text, is_user):  
        if not text.strip():  
            return  
  
        timestamp = datetime.now().strftime("%H:%M")  
        bubble = ChatBubble(text=text.strip(), timestamp=timestamp, size_hint_x=0.7)  
        container = BoxLayout(orientation='horizontal', size_hint_y=None, padding=[dp(15), 0, dp(15), 0])  
        bubble.bind(height=lambda instance, value: setattr(container, 'height', value + dp(30)))  
  
        if is_user:  
            bubble.bg_color = [0.3, 0.6, 1, 1] if not self.is_dark else [0.2, 0.4, 0.8, 1]  
            bubble.text_color = [1, 1, 1, 1]  
            container.add_widget(Widget())  
            container.add_widget(bubble)  
        else:  
            bubble.bg_color = [0.4, 0.9, 0.4, 1] if not self.is_dark else [0.3, 0.7, 0.3, 1]  
            bubble.text_color = [0, 0, 0, 1] if not self.is_dark else [1, 1, 1, 1]  
            container.add_widget(bubble)  
            container.add_widget(Widget())  
  
        self.ids.messages_box.add_widget(container)  
        self.chat_history.append({"text": text.strip(), "is_user": is_user, "timestamp": timestamp})  
  
        if len(self.chat_history) > 100:  
            self.chat_history.pop(0)  
            if self.ids.messages_box.children:  
                self.ids.messages_box.remove_widget(self.ids.messages_box.children[-1])  
  
        Clock.schedule_once(lambda dt: self.scroll_to_bottom(), 0.1)  
  
    def scroll_to_bottom(self):  
        def _scroll(dt):  
            self.ids.scroll_view.scroll_y = 0  
        Clock.schedule_once(_scroll, 0.05)  
  
class ChatApp(App):  
    def build(self):  
        Builder.load_string(KV)  
        return ChatScreen()  
  
if __name__ == '__main__':  
    ChatApp().run()