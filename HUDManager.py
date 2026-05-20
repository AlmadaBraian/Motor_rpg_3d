from EventManager import *
def update_runtime_hud(self):
        if not hasattr(self, "toolkit_ref"):
            return

        tool = self.toolkit_ref

        if not hasattr(tool, "runtime_hint_label"):
            return

        if not hasattr(tool, "runtime_dialog_label"):
            return

        if not tool.play_mode:
            return

        near_npc = get_near_interactive_actor(tool)
        near_evt = get_near_event_cell(tool)

        if near_npc or near_evt:
            tool.runtime_hint_label.config(text="PRESS SPACE")
        else:
            tool.runtime_hint_label.config(text="")

        if (
            tool.dialog_visible
            and tool.dialog_pages
            and tool.dialog_index < len(tool.dialog_pages)
        ):

            txt = tool.dialog_pages[tool.dialog_index]

            if tool.dialog_speaker:
                txt = tool.dialog_speaker + ": " + txt

            tool.runtime_dialog_label.config(text=txt)

        else:
            tool.runtime_dialog_label.config(text="")


    