# window.py
#
# Copyright 2024 walter
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: GPL-3.0-or-later

from gi.repository import Adw
from gi.repository import Gtk, Gio, GLib
import pyttsx4
import os
import shutil
from pygame import mixer
from gtts import gTTS, lang
#from .myvoxpopuli import MyVoice
from voxpopuli import Voice

@Gtk.Template(resource_path='/im/bernard/Paroligilo/window.ui')
class ParoligiloWindow(Adw.ApplicationWindow):
    __gtype_name__ = 'ParoligiloWindow'

    main_text_view = Gtk.Template.Child()  # Feld für Texteingabe
    open_button = Gtk.Template.Child()     # öffnet eine Datei
    tts_chooser = Gtk.Template.Child()     # lädt tts-engine
    read_button = Gtk.Template.Child()     # spielt Audio-Datei ab
    save_button = Gtk.Template.Child()     # speichert Audio-Datei
    lang_chooser= Gtk.Template.Child()     # lädt Sprache
    gender_chooser = Gtk.Template.Child()  # lädt Geschlecht
    speed_chooser= Gtk.Template.Child()    # lädt Sprechgeschwindigkeit

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # die Aktion zum Öffnen einer Datei wird hinzugefügt
        open_action = Gio.SimpleAction(name="open")
        open_action.connect("activate", self.open_file_dialog)
        self.add_action(open_action)

        # die Aktion zum Speichern des Texts wird hinzugefügt
        save_text_action = Gio.SimpleAction(name="save-text-as")
        save_text_action.connect("activate", self.save_text_dialog)
        self.add_action(save_text_action)

        # die Aktion zum Speichern des Audio-files wird hinzugefügt
        save_audio_action = Gio.SimpleAction(name="save-audio-as")
        save_audio_action.connect("activate", self.save_audio_dialog)
        self.add_action(save_audio_action)

        #die Aktion zum Laden der tts-engine wird hinzugefügt
        #self.tts_chooser.connect("notify::selected-item", on_selected_engine)

        #die Aktion zum Hören des Texts wird hinzugefügt
        self.read_button.connect('clicked', self.read_text)

        #die Aktion zum  Speichern des Audio-files wird hinzugefügt
        self.save_button.connect('clicked', self.save_audio_dialog)

    # Dialog zum Öffnen einer Datei wird definiert
    def open_file_dialog(self, action, _):
        # Create a new file selection dialog, using the "open" mode
        native = Gtk.FileDialog()
        native.open(self, None, self.on_open_response)

    # Dialog zum Speichern einer Text-Datei wird definiert
    def save_text_dialog(self, action, _):
        native = Gtk.FileDialog()
        native.save(self, None, self.on_save_text_response)

    # Dialog zum Speichern einer Audio-Datei wird definiert
    def save_audio_dialog(self, action):
        native = Gtk.FileDialog()
        native.save(self, None, self.on_save_audio_response)

    # definiert was geschieht wenn Datei ausgewählt/nicht ausgewählt wurde
    def on_open_response(self, dialog, result):
        file = dialog.open_finish(result)
        # If the user selected a file...
        if file is not None:
            # ... open itgit
            self.open_file(file)

    # definiert was geschieht wenn Text-Datei ausgewählt/nicht ausgewählt wurde
    def on_save_text_response(self, dialog, result):
        file = dialog.save_finish(result)
        if file is not None:
            self.save_text(file)

    # definiert was geschieht wenn Audio-Datei ausgewählt/nicht ausgewählt wurde
    def on_save_audio_response(self, dialog, result):
        file = dialog.save_finish(result)
        if file is not None:
            self.save_audio(file)

    # Inhalt der Textdatei wird asynchron geöffnet um die Anwendung nicht zu blockieren
    def open_file(self, file):
        file.load_contents_async(None, self.open_file_complete)

    # wird aufgerufen wenn das Einlesen fertig oder ein Fehler aufgetreten ist
    def open_file_complete(self, file, result):

        contents = file.load_contents_finish(result)  # enthält boolsche Variable, den eingelesenen Text, u.a.

        if not contents[0]:
            path = file.peek_path()
            print(f"Unable to open {path}: {contents[1]}")
            return

        # Kontrolle ob der eingelesene Inhalt ein Text ist
        try:
            text = contents[1].decode('utf-8')
        except UnicodeError as err:
            path = file.peek_path()
            print(f"Unable to load the contents of {path}: the file is not encoded with UTF-8")
            return

        buffer = self.main_text_view.get_buffer()
        buffer.set_text(text)
        start = buffer.get_start_iter()
        buffer.place_cursor(start)

    def save_text(self, file):
        buffer = self.main_text_view.get_buffer()

        # Retrieve the iterator at the start of the buffer
        start = buffer.get_start_iter()
        # Retrieve the iterator at the end of the buffer
        end = buffer.get_end_iter()
        # Retrieve all the visible text between the two bounds
        text = buffer.get_text(start, end, False)

        # If there is nothing to save, return early
        if not text:
            return

        bytes = GLib.Bytes.new(text.encode('utf-8'))

        # Start the asynchronous operation to save the data into the file
        file.replace_contents_bytes_async(bytes,
                                          None,
                                          False,
                                          Gio.FileCreateFlags.NONE,
                                          None,
                                          self.save_text_complete)

    def save_text_complete(self, file, result):
        res = file.replace_contents_finish(result)
        info = file.query_info("standard::display-name",
                               Gio.FileQueryInfoFlags.NONE)
        if info:
            display_name = info.get_attribute_string("standard::display-name")
        else:
            display_name = file.get_basename()
        if not res:
            print(f"Unable to save {display_name}")

    # Abspielen des Texts
    def read_text(self, button):

        print ('### Audio abspielen   ###')
        buffer = self.main_text_view.get_buffer()

        # Retrieve the iterator at the start of the buffer
        start = buffer.get_start_iter()
        # Retrieve the iterator at the end of the buffer
        end = buffer.get_end_iter()
        # Retrieve all the visible text between the two bounds
        text = buffer.get_text(start, end, False)

        selected_engine = self.tts_chooser.get_selected_item().get_string()
        print(selected_engine)
        engine = selected_engine

        selected_language = self.lang_chooser.get_selected_item().get_string()
        print(selected_language)

        selected_gender = self.gender_chooser.get_selected_item().get_string()
        print(selected_gender)

        selected_speed = self.speed_chooser.get_selected_item().get_string()
        print(selected_speed)

        if engine == 'pyttsx4':
            self.use_pyttsx4(text, selected_language, selected_gender, selected_speed)

        elif engine == 'voxpopuli':
            self.use_voxpopuli(text, selected_language, selected_gender, selected_speed)

        elif engine == 'gTTS':
            # Ausgabe der Audiodatei mit gTTS
            if selected_language == "Deutsch":
                lang = 'de'
            elif selected_language == "Italiano":
                lang = 'it'
            elif selected_language == "English":
                lang = 'en'
            else:
                print ('funktioniert noch nicht')
                return
            self.use_gTTS(text, lang)

        else:
            print ('funktioniert noch nicht')
            return

        # Abspielen der Audiodatei
        mixer.init()
        mixer.music.load("test1.wav")
        mixer.music.play()

    def use_pyttsx4(self,text, lang, gender, speed):

        if lang == "Deutsch":
            lang = 'German'
        elif lang == "Italiano":
            lang = 'Italian'
        elif lang == "English":
            lang = 'English (Great Britain)'
        elif lang == "Esperanto":
            lang = 'Esperanto'
        else:
            print ('funktioniert noch nicht')
            return

        engine = pyttsx4.init()
        voices = engine.getProperty('voices')

        # myVoice = []
        # for voice in voices:
        #     print ('stimmen', voice)
        #     if voice.id == lang:
        #         if len(myVoice) == 0:
        #             myVoice = [voice]
        #         else:
        #             myVoice = [myVoice, voice]
        #         print(myVoice)

        # if len(myVoice) == 0:
        #     print("No voice found for language")
        #     return

        # finalVoice = []
        # if gender == "F":
        #     gender = "female"
        # else:
        #     gender = "male"
        # for voice in myVoice:
        #     if voice.gender == gender:
        #         finalVoice = [voice]
        #         break

        # if len(finalVoice) == 0:
        #     print("No voice found for language")
        #     return

        engine.setProperty('voice', lang)
        rate = int(speed)
        engine.setProperty('rate', rate)
        engine.save_to_file(text, 'test1.wav')
        engine.runAndWait()

    def use_voxpopuli(self,text, lang, gender, speed):
        if lang == "Deutsch":
            lang = 'de'
        elif lang == "Italiano":
            lang = 'it'
        elif lang == "English":
            lang = 'en'
        else:
            print ('funktioniert noch nicht')
            return
        voice = Voice(lang =lang)
        print ('Sprache', lang)
        wav = voice.to_audio(text)
        print ('jetzt ist der wav', wav)
        with open("test1.wav", "wb") as wavfile:
            wavfile.write(wav)
        print ('der audiofile', 'test1.wav')

    def use_gTTS(self,text, lang):

        tts = gTTS(text, lang=lang, slow=True)
        tts.save('test1.mp3')

    # Dialog zum Speichern des Audio-files
    def save_audio(self, file):
        #print ('#### Audio speichern   ####')
        shutil.move('test1.mp3',file)


