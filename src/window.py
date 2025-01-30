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
from pygame import mixer
from gtts import gTTS, lang

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

    # definiert was geschieht wenn Datei ausgewählt/nicht ausgewählt wurde
    def on_open_response(self, dialog, result):
        file = dialog.open_finish(result)
        # If the user selected a file...
        if file is not None:
            # ... open it
            self.open_file(file)

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
            # Ausgabe auf Audiodatei mit pyttsx4
            if selected_language == "Deutsch":
                lang = 'German'
            elif selected_language == "Italiano":
                lang = 'Italian'
            elif selected_language == "English":
                lang = 'English (Great Britain)'
            elif selected_language == "Esperanto":
                lang = 'Esperanto'
            else:
                print ('funktioniert noch nicht')
                return
            gender = selected_gender
            speed = selected_speed

            self.use_pyttsx4(text, lang, gender, speed)

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
        mixer.music.load("test1.mp3")
        mixer.music.play()

    def use_pyttsx4(self,text, lang, gender, speed):
        engine = pyttsx4.init()
        #voices = engine.getProperty('voices')
        #for voice in voices:
            #print(voice, voice.id)
        if gender == 'F':
            lang = lang + 'f4'

        engine.setProperty('voice', lang)
        rate = int(speed)
        engine.setProperty('rate', rate)
        engine.save_to_file(text, 'test1.mp3')
        engine.runAndWait()

    def use_gTTS(self,text, lang):

        tts = gTTS(text, lang=lang)
        tts.save('test1.mp3')

    # Dialog zum Speichern des Audio-files
    def save_audio_dialog(self, button):
        print ('#### Audio speichern   ####')



