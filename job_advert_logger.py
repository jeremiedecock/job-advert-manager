#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (c) 2015 Jérémie DECOCK (http://www.jdhp.org)

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

"""
...
"""

from gi.repository import Gtk as gtk
from gi.repository import Pango as pango

import datetime
import fcntl  # TODO: use GtkApplication instead
import json
import sys

JSON_FILENAME = "job_adverts.json"

TREE_VIEW_COLUMN_LABEL_LIST = ["Category", "Organization", "Note", "Date", "Url", "Title"]

CATEGORY_LIST = ["Entrprise", "IR/IE", "PostDoc"]
NOTE_LIST = ["0", "1", "2", "3", "4", "5"]

JOB_ADVERT_WEB_SITES = ['<a href="http://www.inria.fr/institut/recrutement-metiers/offres">Inria</a>',
                        '<a href="https://flowers.inria.fr/jobs/">Inria - Flowers team</a>',
                        '<a href="http://www.ademe.fr/lademe-recrute">Ademe</a>',
                        '<a href="http://moorea.cea.fr/Web/ListeDoss.aspx">CEA</a>',
                        '<a href="https://jobs.github.com/positions">GitHub Jobs</a>',
                        '<a href="http://careers.stackoverflow.com/jobs">Stackoverflow Careers</a>']

LOCK_FILENAME = ".lock"  # TODO: use GtkApplication instead

class MainWindow(gtk.Window):

    def __init__(self):

        # Load the JSON database
        self.json_database = {}
        try:
            fd = open(JSON_FILENAME, "r")
            self.json_database = json.load(fd)
            fd.close()
        except:
            pass

        # Build the main window
        gtk.Window.__init__(self, title="Job advert logger")
        self.maximize()
        self.set_border_width(4)

        notebook_container = gtk.Notebook()
        self.add(notebook_container)

        # Add job advert container ############################################

        self.add_category_combobox = gtk.ComboBoxText()
        self.add_organization_entry = gtk.Entry()
        self.add_url_entry = gtk.Entry()
        self.add_title_entry = gtk.Entry()
        self.add_note_combobox = gtk.ComboBoxText()
        self.add_pros_textview = gtk.TextView()
        self.add_cons_textview = gtk.TextView()
        self.add_desc_textview = gtk.TextView()

        add_widget_dict = {"category_widget": self.add_category_combobox,
                           "organization_widget": self.add_organization_entry,
                           "url_widget": self.add_url_entry,
                           "title_widget": self.add_title_entry,
                           "note_widget": self.add_note_combobox,
                           "pros_widget": self.add_pros_textview,
                           "cons_widget": self.add_cons_textview,
                           "desc_widget": self.add_desc_textview}

        add_container = self.make_job_advert_add_and_edit_container(add_widget_dict, self.add_job_advert_cb, self.clear_job_adverts_add_form_cb)

        # Edit container ######################################################

        paned_container = gtk.Paned(orientation = gtk.Orientation.VERTICAL)

        # The position in pixels of the divider (i.e. the default size of the top pane)
        paned_container.set_position(400)

        # Creating the ListStore model
        self.liststore = gtk.ListStore(str, str, int, str, str, str)
        for url, job_advert_dict in self.json_database.items():
            category = job_advert_dict["category"]
            organization = job_advert_dict["organization"]
            note = int(job_advert_dict["note"])
            title = job_advert_dict["title"]
            date = job_advert_dict["date"]

            self.liststore.append([category, organization, note, date, url, title])

        # Creating the treeview, making it use the filter as a model, and
        # adding the columns
        treeview = gtk.TreeView(self.liststore)
        for column_index, column_title in enumerate(TREE_VIEW_COLUMN_LABEL_LIST):
            renderer = gtk.CellRendererText()

            if column_title in ("Url", "Title"):
                renderer.set_property("ellipsize", pango.EllipsizeMode.END)
                renderer.set_property("ellipsize-set", True)

            column = gtk.TreeViewColumn(column_title, renderer, text=column_index)
            column.set_resizable(True)       # Let the column be resizable

            if column_title == "Category":
                column.set_sort_column_id(0)
            elif column_title == "Organization":
                column.set_sort_column_id(1)
            elif column_title == "Note":
                column.set_sort_column_id(2)
            elif column_title == "Date":
                column.set_sort_column_id(3)
            elif column_title == "Url":
                column.set_sort_column_id(4)
            elif column_title == "Title":
                column.set_sort_column_id(5)

            treeview.append_column(column)

        select = treeview.get_selection()
        select.connect("changed", self.treeview_selection_changed_cb)

        # Scrolled window
        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_border_width(18)
        scrolled_window.set_shadow_type(gtk.ShadowType.IN)
        scrolled_window.set_policy(gtk.PolicyType.AUTOMATIC, gtk.PolicyType.ALWAYS)
        scrolled_window.add(treeview)

        # Edit box container
        self.edit_category_combobox = gtk.ComboBoxText()
        self.edit_organization_entry = gtk.Entry()
        self.edit_url_entry = gtk.Entry()
        self.edit_url_entry.set_editable(False)
        self.edit_title_entry = gtk.Entry()
        self.edit_note_combobox = gtk.ComboBoxText()
        self.edit_pros_textview = gtk.TextView()
        self.edit_cons_textview = gtk.TextView()
        self.edit_desc_textview = gtk.TextView()

        edit_widget_dict = {"category_widget": self.edit_category_combobox,
                            "organization_widget": self.edit_organization_entry,
                            "url_widget": self.edit_url_entry,
                            "title_widget": self.edit_title_entry,
                            "note_widget": self.edit_note_combobox,
                            "pros_widget": self.edit_pros_textview,
                            "cons_widget": self.edit_cons_textview,
                            "desc_widget": self.edit_desc_textview}

        edit_container = self.make_job_advert_add_and_edit_container(edit_widget_dict, self.edit_job_advert_cb, self.reset_job_adverts_edit_form_cb)

        # Add the widgets to the container
        paned_container.add1(scrolled_window)
        paned_container.add2(edit_container)

        # Search container ####################################################

        search_container = gtk.Box(orientation = gtk.Orientation.VERTICAL, spacing=6)
        search_container.set_border_width(18)

        web_sites_label = gtk.Label()
        web_sites_label.set_markup("\n".join(JOB_ADVERT_WEB_SITES))
        search_container.pack_start(web_sites_label, expand=True, fill=True, padding=0)

        ###################################

        add_label = gtk.Label(label="Add")
        notebook_container.append_page(add_container, add_label)

        edit_label = gtk.Label(label="Edit")
        notebook_container.append_page(paned_container, edit_label)

        search_label = gtk.Label(label="Search")
        notebook_container.append_page(search_container, search_label)


    def make_job_advert_add_and_edit_container(self, widget_dict, save_function, clear_function):
        """
        ...
        """

        category_combobox = widget_dict["category_widget"]
        organization_entry = widget_dict["organization_widget"]
        url_entry = widget_dict["url_widget"]
        title_entry = widget_dict["title_widget"]
        note_combobox = widget_dict["note_widget"]
        pros_textview = widget_dict["pros_widget"]
        cons_textview = widget_dict["cons_widget"]
        desc_textview = widget_dict["desc_widget"]

        add_box_container = gtk.Box(orientation = gtk.Orientation.VERTICAL, spacing=6)
        add_box_container.set_border_width(18)

        # Category
        category_label = gtk.Label(label="Category")
        category_combobox.set_entry_text_column(0)
        for category in CATEGORY_LIST:
            category_combobox.append_text(category)
        category_combobox.set_active(0)
        category_box_container = gtk.Box(spacing=12)
        category_box_container.pack_start(category_label, expand=False, fill=True, padding=0)
        category_box_container.pack_start(category_combobox, expand=True, fill=True, padding=0)

        # Organization
        organization_label = gtk.Label(label="Organization")
        organization_box_container = gtk.Box(spacing=12)
        organization_box_container.pack_start(organization_label, expand=False, fill=True, padding=0)
        organization_box_container.pack_start(organization_entry, expand=True, fill=True, padding=0)

        # URL
        url_label = gtk.Label(label="Url")
        url_box_container = gtk.Box(spacing=12)
        url_box_container.pack_start(url_label, expand=False, fill=True, padding=0)
        url_box_container.pack_start(url_entry, expand=True, fill=True, padding=0)

        # Title
        title_label = gtk.Label(label="Title")
        title_box_container = gtk.Box(spacing=12)
        title_box_container.pack_start(title_label, expand=False, fill=True, padding=0)
        title_box_container.pack_start(title_entry, expand=True, fill=True, padding=0)

        # Note
        note_label = gtk.Label(label="Note")
        note_combobox.set_entry_text_column(0)
        for note in NOTE_LIST:
            note_combobox.append_text(note)
        note_combobox.set_active(len(NOTE_LIST)-1)
        #note_entry.set_max_length(1)
        note_box_container = gtk.Box(spacing=12)
        note_box_container.pack_start(note_label, expand=False, fill=True, padding=0)
        note_box_container.pack_start(note_combobox, expand=True, fill=True, padding=0)

        # Pros
        pros_label = gtk.Label(label="Pros")
        pros_label.set_alignment(0, 0.5) # Align left

        pros_textview.set_wrap_mode(gtk.WrapMode.WORD)

        pros_scrolled_window = gtk.ScrolledWindow()
        pros_scrolled_window.set_border_width(3)
        pros_scrolled_window.set_shadow_type(gtk.ShadowType.OUT)
        pros_scrolled_window.set_policy(gtk.PolicyType.AUTOMATIC, gtk.PolicyType.ALWAYS)
        pros_scrolled_window.add(pros_textview)

        # Cons
        cons_label = gtk.Label(label="Cons")
        cons_label.set_alignment(0, 0.5) # Align left

        cons_textview.set_wrap_mode(gtk.WrapMode.WORD)

        cons_scrolled_window = gtk.ScrolledWindow()
        cons_scrolled_window.set_border_width(3)
        cons_scrolled_window.set_shadow_type(gtk.ShadowType.OUT)
        cons_scrolled_window.set_policy(gtk.PolicyType.AUTOMATIC, gtk.PolicyType.ALWAYS)
        cons_scrolled_window.add(cons_textview)

        # Description
        desc_label = gtk.Label(label="Description")
        desc_label.set_alignment(0, 0.5) # Align left

        desc_textview.set_wrap_mode(gtk.WrapMode.WORD)

        desc_scrolled_window = gtk.ScrolledWindow()
        desc_scrolled_window.set_border_width(3)
        desc_scrolled_window.set_shadow_type(gtk.ShadowType.OUT)
        desc_scrolled_window.set_policy(gtk.PolicyType.AUTOMATIC, gtk.PolicyType.ALWAYS)
        desc_scrolled_window.add(desc_textview)

        # Buttons
        add_button = gtk.Button(label="Save")
        add_button.connect("clicked", save_function)
        cancel_button = gtk.Button(label="Cancel")
        cancel_button.connect("clicked", clear_function)
        btn_box_container = gtk.Box(spacing=12)
        btn_box_container.pack_start(add_button, expand=True, fill=True, padding=0)
        btn_box_container.pack_start(cancel_button, expand=True, fill=True, padding=0)

        # Add the widgets to the container
        add_box_container.pack_start(category_box_container, expand=False, fill=True, padding=0)
        add_box_container.pack_start(organization_box_container, expand=False, fill=True, padding=0)
        add_box_container.pack_start(url_box_container, expand=False, fill=True, padding=0)
        add_box_container.pack_start(title_box_container, expand=False, fill=True, padding=0)
        add_box_container.pack_start(note_box_container, expand=False, fill=True, padding=0)
        add_box_container.pack_start(pros_label, expand=False, fill=True, padding=0)
        add_box_container.pack_start(pros_scrolled_window, expand=True, fill=True, padding=0)
        add_box_container.pack_start(cons_label, expand=False, fill=True, padding=0)
        add_box_container.pack_start(cons_scrolled_window, expand=True, fill=True, padding=0)
        add_box_container.pack_start(desc_label, expand=False, fill=True, padding=0)
        add_box_container.pack_start(desc_scrolled_window, expand=True, fill=True, padding=0)
        add_box_container.pack_start(btn_box_container, expand=False, fill=True, padding=0)

        return add_box_container


    def add_job_advert_cb(self, widget):
        """
        Save the "add job advert" form.
        """

        # Get data from entry widgets ###########

        category = self.add_category_combobox.get_active_text()

        organization = self.add_organization_entry.get_text()

        url = self.add_url_entry.get_text()

        title = self.add_title_entry.get_text()

        note = self.add_note_combobox.get_active_text()

        pros_buffer = self.add_pros_textview.get_buffer()
        pros = pros_buffer.get_text(pros_buffer.get_start_iter(), pros_buffer.get_end_iter(), True)

        cons_buffer = self.add_cons_textview.get_buffer()
        cons = cons_buffer.get_text(cons_buffer.get_start_iter(), cons_buffer.get_end_iter(), True)

        desc_buffer = self.add_desc_textview.get_buffer()
        desc = desc_buffer.get_text(desc_buffer.get_start_iter(), desc_buffer.get_end_iter(), True)

        date = datetime.date.isoformat(datetime.date.today())

        # Check data ############################

        error_msg_list = []

        if category is None:
            error_msg_list.append("You must select a category.")

        if len(url) == 0:
            error_msg_list.append("You must enter an url.")
        elif url in self.json_database:
            error_msg_list.append("This job advert already exists in the database.")

        if note is None:
            error_msg_list.append("You must select a note.")
        else:
            try:
                if int(note) not in range(6):
                    error_msg_list.append("The note must be a number between 0 and 5.")
            except:
                error_msg_list.append("The note must be a number between 0 and 5.")

        # Save data or display error ############

        if len(error_msg_list) == 0:
            job_advert_dict = {"date": date,
                               "category": category,
                               "organization": organization,
                               "title": title,
                               "note": note,
                               "pros": pros,
                               "cons": cons,
                               "desc": desc}

            # Save the job advert in the database
            self.json_database[url] = job_advert_dict

            # Save the job advert in the JSON file
            with open(JSON_FILENAME, "w") as fd:
                json.dump(self.json_database, fd, sort_keys=True, indent=4)

            # Update the GtkListStore (TODO: redundant with the previous JSON data structure)
            self.liststore.append([category, organization, int(note), date, url, title])

            # Clear all entries (except "category_entry")
            self.clear_job_adverts_add_form_cb()
        else:
            dialog = gtk.MessageDialog(self, 0, gtk.MessageType.ERROR, gtk.ButtonsType.OK, "Error")
            dialog.format_secondary_text("".join(error_msg_list))
            dialog.run()
            dialog.destroy()


    def clear_job_adverts_add_form_cb(self, widget=None):
        """
        Clear the current form: reset the entry widgets to their default value.
        """

        # Clear all entries except "add_category_combobox" and "add_organization_entry"
        self.add_url_entry.set_text("")
        #self.add_organization_entry.set_text("")
        self.add_title_entry.set_text("")
        self.add_note_combobox.set_active(len(NOTE_LIST)-1)
        self.add_pros_textview.get_buffer().set_text("")
        self.add_cons_textview.get_buffer().set_text("")
        self.add_desc_textview.get_buffer().set_text("")


    def treeview_selection_changed_cb(self, selection):
        model, treeiter = selection.get_selected()
        if treeiter != None:
            url = self.liststore[treeiter][4]
            self.reset_job_adverts_edit_form_cb(widget=None, url=url)


    def edit_job_advert_cb(self, widget):
        """
        Save the current form.
        """

        pass # TODO!!!


    def reset_job_adverts_edit_form_cb(self, widget=None, url=None):
        """
        Clear the current form: reset the entry widgets to their default value.
        """

        if url is None:
            self.edit_url_entry.set_text("")
            #self.edit_category_combobox.set_active(...) # TODO!!!
            self.edit_organization_entry.set_text("")
            #self.edit_note_combobox.set_active(len(NOTE_LIST)-1) # TODO!!!
            self.edit_title_entry.set_text("")
            self.edit_pros_textview.get_buffer().set_text("")
            self.edit_cons_textview.get_buffer().set_text("")
            self.edit_desc_textview.get_buffer().set_text("")
        else:
            category = self.json_database[url]["category"]
            organization = self.json_database[url]["organization"]
            note = self.json_database[url]["note"]
            title = self.json_database[url]["title"]
            #date = self.json_database[url]["date"]
            pros = self.json_database[url]["pros"]
            cons = self.json_database[url]["cons"]
            desc = self.json_database[url]["desc"]

            self.edit_url_entry.set_text(url)
            #self.edit_category_combobox.set_active(...) # TODO!!!
            self.edit_organization_entry.set_text(organization)
            #self.edit_note_combobox.set_active(len(NOTE_LIST)-1) # TODO!!!
            self.edit_title_entry.set_text(title)
            self.edit_pros_textview.get_buffer().set_text(pros)
            self.edit_cons_textview.get_buffer().set_text(cons)
            self.edit_desc_textview.get_buffer().set_text(desc)


def main():

    # Acquire an exclusive lock on LOCK_FILENAME
    fd = open(LOCK_FILENAME, "w")  # TODO: use GtkApplication instead

    try:  # TODO: use GtkApplication instead
        # LOCK_EX = acquire an exclusive lock on fd
        # LOCK_NB = make a nonblocking request
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)  # TODO: use GtkApplication instead

        ###################################

        window = MainWindow()

        window.connect("delete-event", gtk.main_quit) # ask to quit the application when the close button is clicked
        window.show_all()                             # display the window
        gtk.main()                                    # GTK+ main loop

        ###################################

        # LOCK_UN = unlock fd
        fcntl.flock(fd, fcntl.LOCK_UN)  # TODO: use GtkApplication instead
    except IOError:  # TODO: use GtkApplication instead
        #print(LOCK_FILENAME + " is locked ; another instance is running. Exit.")
        dialog = gtk.MessageDialog(parent=None, flags=0, message_type=gtk.MessageType.ERROR, buttons=gtk.ButtonsType.OK, message_format="Another instance is running in the same directory")
        dialog.format_secondary_text("Exit.")
        dialog.run()
        dialog.destroy()

        sys.exit(1)


if __name__ == '__main__':
    main()
