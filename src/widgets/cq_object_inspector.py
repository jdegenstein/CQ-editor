from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem, QAction
from PyQt5.QtCore import Qt, pyqtSlot, pyqtSignal

from OCC.AIS import AIS_ColoredShape, AIS_Line, AIS_Plane
from OCC.Quantity import Quantity_NOC_RED as RED
from OCC.Quantity import Quantity_NOC_GREEN as GREEN
from OCC.Quantity import Quantity_NOC_BLUE1 as BLUE
from OCC.Geom import Geom_CylindricalSurface, Geom_Plane, Geom_Circle,\
     Geom_TrimmedCurve, Geom_Axis1Placement, Geom_Axis2Placement, Geom_Line
from OCC.gp import gp_Trsf, gp_Vec, gp_Ax3, gp_Dir, gp_Pnt, gp_Ax1, gp_Pln

from OCC.BRepBuilderAPI import BRepBuilderAPI_MakeFace

from cadquery import Vector

from ..mixins import ComponentMixin
from ..icons import icon


        
class CQChildItem(QTreeWidgetItem):
    
    def __init__(self,cq_item,**kwargs):
        
        super(CQChildItem,self).\
            __init__([type(cq_item).__name__,str(cq_item)],**kwargs)
        
        self.cq_item = cq_item

class CQStackItem(QTreeWidgetItem):
    
    def __init__(self,name,workplane=None,**kwargs):
        
        super(CQStackItem,self).__init__([name,''],**kwargs)
        
        self.workplane = workplane


class CQObjectInspector(QTreeWidget,ComponentMixin):
    
    name = 'CQ Object Inspector'
    
    sigRemoveObjects = pyqtSignal(list)
    sigDisplayObjects = pyqtSignal(list,bool)
    
    def  __init__(self,parent):
        
        super(CQObjectInspector,self).__init__(parent)   
        self.setHeaderHidden(False)
        self.setRootIsDecorated(True)
        self.setContextMenuPolicy(Qt.ActionsContextMenu)
        self.setColumnCount(2)
        
        self.root = self.invisibleRootItem()
        self.inspected_items = []
        
        self._toolbar_actions = \
            [QAction(icon('inspect'),'Clear all',self,\
                     toggled=self.inspect,checkable=True)]
        
        self.addActions(self._toolbar_actions)
        
    def menuActions(self):
        
        return {}
    
    def toolbarActions(self):
        
        return self._toolbar_actions
    
    @pyqtSlot(bool)
    def inspect(self,value):
        
        if value:
            self.itemSelectionChanged.connect(self.handleSelection)
            self.itemSelectionChanged.emit()
        else:
            self.itemSelectionChanged.disconnect(self.handleSelection)
            self.sigRemoveObjects.emit(self.inspected_items)
            
    @pyqtSlot()    
    def handleSelection(self):
        
        inspected_items = self.inspected_items
        self.sigRemoveObjects.emit(inspected_items)
        inspected_items.clear()
        
        items = self.selectedItems()
        if len(items) == 0:
            return
        
        item = items[-1]
        if type(item) is CQStackItem:
            cq_plane = item.workplane.plane
            plane = gp_Pln(cq_plane.origin.toPnt(),cq_plane.zDir.toDir())
            face = BRepBuilderAPI_MakeFace(plane,-10,10,-10,10).Face()
            ais_plane = AIS_ColoredShape(face)
            ais_plane.SetTransparency(0.9)
            ais_plane.SetColor(BLUE)
            
            inspected_items.append(ais_plane)
            
            for child in (item.child(i) for i in range(item.childCount())):
                obj = child.cq_item
                if hasattr(obj,'wrapped') and type(obj) != Vector:
                    ais = AIS_ColoredShape(obj.wrapped)
                    inspected_items.append(ais)
                
        else:
            obj = item.cq_item
            if hasattr(obj,'wrapped') and type(obj) != Vector:
                ais = AIS_ColoredShape(obj.wrapped)
                inspected_items.append(ais)
            
        self.sigDisplayObjects.emit(inspected_items,False)
    
    @pyqtSlot(object)
    def setObject(self,cq_obj):
        
        self.root.takeChildren()

        while cq_obj.parent:
            current_frame = CQStackItem(str(cq_obj.plane.origin),workplane=cq_obj)
            self.root.addChild(current_frame)
            
            for obj in cq_obj.objects:
                current_frame.addChild(CQChildItem(obj))
            
            cq_obj = cq_obj.parent
            
            