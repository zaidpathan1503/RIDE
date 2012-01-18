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


if __name__ == '__main__':
    class MyFrame(wx.Frame):
        def __init__(self, parent, id, title):
            wx.Frame.__init__(self, parent, id, title)
    class MyMenuApp(wx.App):
        def OnInit(self):
            frame = MyFrame(None , -1, 'Frame Window Demo')
            sz = wx.BoxSizer()
            tree2 = FileSystemTree(frame)
            root = tree2.AddRoot('root', image=tree2.images.PAGE_WHITE_GEAR)
            for x in range(5):
                node = tree2.AppendItem(root, 'Item %d' % x, image=tree2.images.FOLDER_WRENCH)
                for y in range(3):
                    tree2.AppendItem(node, 'Child %d' % y, image=tree2.images.ROBOT)
            sz.Add(tree2, 0, wx.GROW|wx.ALL, 5)
            frame.Show(True)
            self.SetTopWindow(frame)
            return True
    # Run program
    app=MyMenuApp(0)
    app.MainLoop()



