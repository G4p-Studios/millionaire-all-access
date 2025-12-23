# accessible_output.py

from accessible_output2.outputs.auto import Auto

# Initialize the screen reader output
speaker = Auto()

def speak(text, interrupt=True):
    """
    Speaks the given text using the screen reader.
    :param text: The text to be spoken.
    :param interrupt: If True, it will stop any ongoing speech.
    """
    try:
        speaker.speak(text, interrupt=interrupt)
    except Exception as e:
        # This can happen if no screen reader is running
        print(f"Could not speak: {e}")

def stop_speech():
    """
    Stops any currently speaking output.
    """
    try:
        # This is not directly supported in the same way, but speaking an empty
        # string with interrupt=True effectively silences it.
        speaker.speak("", interrupt=True)
    except Exception as e:
        print(f"Could not stop speech: {e}")

# Announce that the module is ready when the game starts
speak("Accessibility module initialized.")