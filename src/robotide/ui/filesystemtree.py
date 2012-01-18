#  Copyright 2008-2012 Nokia Siemens Networks Oyj
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

# Configure wx version to allow running test app in __main__
import os


if __name__ == '__main__':
    import robotide as _

import wx
from robotide.ui.images import TreeImageList


try:
    import wx.lib.agw.customtreectrl as CT
except ImportError:
    import wx.lib.customtreectrl as CT


class FileSystemTree(CT.CustomTreeCtrl):

    def __init__(self, parent):
        CT.CustomTreeCtrl.__init__(self, parent=parent, name=self.__class__.__name__)
        self.images = TreeImageList()
        self.SetImageList(self.images)


class FileSystemTreeController(object):

    def __init__(self, file_system_tree):
        self._tree = file_system_tree
        self._closed_directories = []
        self._tree.Bind(wx.EVT_TREE_ITEM_EXPANDING, self._expanding)

    def _expanding(self, event):
        item = event.GetItem()
        self._tree.DeleteChildren(item)
        self._populate_directory(item)

    def populate_tree(self, directory):
        root = self._tree.AddRoot(text=os.path.basename(directory), image=self._tree.images.FOLDER, data=directory)
        self._tree.AppendItem(root, text='...')

    def _populate_directory(self, directory_node):
        files, dirs = self._get_directory_child_elements(directory_node.GetData())
        for d in dirs:
            self._add_directory(d, directory_node)
        for f in files:
            self._tree.AppendItem(directory_node, text=f, image=self._tree.images.PAGE_WHITE)

    def _add_directory(self, directory_name, parent_node):
        directory = self._tree.AppendItem(parent_node, text=directory_name, image=self._tree.images.FOLDER, data=os.path.join(parent_node.GetData(), directory_name))
        self._tree.AppendItem(directory, text='...')
        self._closed_directories.append(directory)

    def _get_directory_child_elements(self, directory):
        dirs = []
        files = []
        for item in os.listdir(directory):
            if os.path.isfile(os.path.join(directory, item)):
                files += [item]
            else:
                dirs += [item]
        return sorted(files), sorted(dirs)


if __name__ == '__main__':
    class MyFrame(wx.Frame):
        def __init__(self, parent, id, title):
            wx.Frame.__init__(self, parent, id, title)
    class MyMenuApp(wx.App):
        def OnInit(self):
            frame = MyFrame(None , -1, 'Frame Window Demo')
            sz = wx.BoxSizer()
            tree2 = FileSystemTree(frame)
            FileSystemTreeController(tree2).populate_tree(os.path.split(__file__)[0]+'/..')
            sz.Add(tree2, 0, wx.GROW|wx.ALL, 5)
            frame.Show(True)
            self.SetTopWindow(frame)
            return True
    # Run program
    app=MyMenuApp(0)
    app.MainLoop()



