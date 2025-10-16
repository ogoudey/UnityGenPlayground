#
#   Option 3 for a GUI
#   A desktop app with a nice GUI
#
#   kind of unclear what the pros are
#

import PySimpleGUI as sg
import random
import time
# Sample data for the table
world_names = [
    "World 1", "World 2", "World 3", "World 4", "World 5",
    "World Alpha", "World Beta", "World Gamma", "World Delta"
]

def random_worlds():
    count = random.randint(1, 4)
    return random.sample(world_names, count)

data = {
    "Generation A": {"date": "10/30/2025", "data": {"worlds": random_worlds()}},
    "Generation B": {"date": "10/12/2025", "data": {"worlds": random_worlds()}},
    "Generation C": {"date": "9/28/2025", "data": {"worlds": random_worlds()}},
    "Generation D": {"date": "10/20/2025", "data": {"worlds": random_worlds()}},
    "Generation E": {"date": "10/20/2025", "data": {"worlds": random_worlds()}},
    "Generation G": {"date": "10/20/2025", "data": {"worlds": random_worlds()}}
}

# Table headings
headings = ["Generation", "Date"]


spinner_states = ["|", "/", "-", "\\"]
generated_text_from_agents = "Thinking..."

# Track selected generation
selected_generation = list(data.keys())[0]  # Default to first generation

# Layout
layout = [
    [sg.Text("Prompt:"), sg.Input(key="-PROMPT-", size=(30,1)), sg.Button("Generate...", key="-INPUT-", size=(16,1))],
    [sg.Text("Generated text will appear here", key="-OUTPUT-", visible=False)],  # initially hidden
    [sg.Frame("Generated worlds:",
              [[sg.Table(
                  values=[[gen, info["date"]] for gen, info in data.items()],
                  headings=headings, 
                  display_row_numbers=False,
                  auto_size_columns=False, col_widths=[20, 16],
                  justification='left',
                  key="-TABLE-",
                  enable_events=True,
                  row_height=30,
                  num_rows=4
              )]],
              pad=(10,10)),

     sg.Frame("Inspector",
              [[sg.Multiline("", size=(25, 10), key="-INSPECTOR-", disabled=True)]],
              pad=(5,5))],
    [sg.Text(f"Check {selected_generation} for compatibility", key="-STATUS-"), sg.Button("Check...", key="-CHECK-")],
    [sg.Button("Launch")]
]

# Create window
window = sg.Window("World Generator 0.0", layout, size=(640, 480), finalize=True)
print(window)
# Event loop
while True:
    event, values = window.read()
    print(event)
    if event == sg.WIN_CLOSED:
        break
    elif event == "-INPUT-":
        window["-OUTPUT-"].update(visible=True)
        # Example: fill it with something based on input
        prompt_text = values["-PROMPT-"]
        print(f"Taking {prompt_text}")
        generated_text = f"{generated_text_from_agents}"
        window["-OUTPUT-"].update(generated_text)

        # This should run in another thread and get updates on generated_text_from_agents.
        for i in range(20):
            spinner = spinner_states[i % 4]
            window["-INPUT-"].update(f"{spinner}")
            window.refresh()
            time.sleep(0.1)

    elif event == "-TABLE-":
    # Update inspector panel based on selection
        selected = values["-TABLE-"]
        if selected:
            gen_idx = selected[0]
            gen_name = list(data.keys())[gen_idx]
            gen_info = data[gen_name]
            worlds = gen_info["data"]["worlds"]
            worlds_str = "\n".join([f"{i+1}. {world}" for i, world in enumerate(worlds)])
            window["-INSPECTOR-"].update(
            f"Generation: {gen_name}\nDate: {gen_info['date']}\nWorlds:\n{worlds_str}"
            )
            window["-STATUS-"].update(f"Check {gen_name} for compatibility")
    elif event == "Launch":
        selected = values["-TABLE-"]
        if selected:
            gen_idx = selected[0]
            gen_name = list(data.keys())[gen_idx]
            sg.popup(f"Launching {gen_name}...")

window.close()
