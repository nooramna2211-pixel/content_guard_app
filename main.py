from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.utils import platform

class ContentGuardApp(App):
    def build(self):
        layout = BoxLayout(orientation='vertical', padding=20, spacing=20)
        
        lbl = Label(
            text="Content Guard Active\nProtecting your device 24/7",
            font_size='20sp',
            halign='center'
        )
        layout.add_widget(lbl)
        
        btn_admin = Button(
            text="Enable Anti-Uninstall Protection",
            size_hint=(1, 0.2),
            background_color=(0.2, 0.6, 0.2, 1)
        )
        btn_admin.bind(on_press=self.enable_device_admin)
        layout.add_widget(btn_admin)
        
        return layout

    def on_start(self):
        self.enable_device_admin(None)

    def enable_device_admin(self, instance):
        if platform == 'android':
            try:
                from jnius import autoclass
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                DevicePolicyManager = autoclass('android.app.admin.DevicePolicyManager')
                Intent = autoclass('android.content.Intent')

                activity = PythonActivity.mActivity
                intent = Intent(DevicePolicyManager.ACTION_ADD_DEVICE_ADMIN)
                activity.startActivity(intent)
            except Exception as e:
                print("Android Admin Intent Error:", e)

if __name__ == '__main__':
    ContentGuardApp().run()