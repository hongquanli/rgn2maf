import xml.etree.ElementTree as ET

# comment
# XYZStagePointDefinitionList.append(ET.Comment('Leica Application Suite X (LAS X)'))
# XYZStagePointDefinitionList.append(ET.Comment('Leica Microsystems CMS GmbH'))
# XYZStagePointDefinitionList.append(ET.Comment('http://www.confocal-microscopy.com'))
# XYZStagePointDefinitionList.append(ET.Comment('LAS X 3.5.5.19976'))

ZMode = '2'
ZUseModeName = 'z-wide'
ValidStack = '0'
Sections = '1'
StepSize = '0'
PositionIdentifier = 'Position1'
PositionID = 'PositionID'
MartixIdentifier = '0'
TileScanIdentifier = '0'
additionalzposition_Valid = '1'
additionalzposition_SuperZMode = '1'
additionalzposition_SuperZModeName = 'RestrictedRange'
additionalzposition_ZMode = '2'
additionalzposition_ZUseModeName = 'z-wide'
additionalzposition_ZPosition = '0.0012599877'

class XYZStagePointDefinitionList:
	def __init__(self):
		# top element
		self.top_element = ET.Element('XYZStagePointDefinitionList')
		self.top_element.set('StageOrderNumber','0')

	def add_point(self,x_pos,y_pos,AFCOffset,ZPosition):
		XYZStagePointDefinition = ET.SubElement(self.top_element,'XYZStagePointDefinition')
		XYZStagePointDefinition.set('StageXPos',str(x_pos))
		XYZStagePointDefinition.set('StageYPos',str(y_pos))
		XYZStagePointDefinition.set('ZMode',ZMode)
		XYZStagePointDefinition.set('ZUseModeName',ZUseModeName)
		XYZStagePointDefinition.set('Sections',Sections)
		XYZStagePointDefinition.set('StepSize',StepSize)
		XYZStagePointDefinition.set('PositionIdentifier',PositionIdentifier)
		XYZStagePointDefinition.set('PositionID',PositionID)
		XYZStagePointDefinition.set('MartixIdentifier',MartixIdentifier)
		XYZStagePointDefinition.set('TileScanIdentifier',TileScanIdentifier)
		XYZStagePointDefinition.set('AFCOffset',str(AFCOffset))
		AdditionalZPositionList = ET.SubElement(XYZStagePointDefinition,'AdditionalZPositionList')
		AdditionalZPosition = ET.SubElement(AdditionalZPositionList,'AdditionalZPosition')
		AdditionalZPosition.set('Valid',additionalzposition_Valid)
		AdditionalZPosition.set('SuperZMode',additionalzposition_SuperZMode)
		AdditionalZPosition.set('SuperZModeName',additionalzposition_SuperZModeName)
		AdditionalZPosition.set('ZMode',additionalzposition_ZMode)
		AdditionalZPosition.set('ZUseModeName',additionalzposition_ZUseModeName)
		AdditionalZPosition.set('ZPosition',str(ZPosition))

	def export(self,filename = 'XYZStagePointDefinitionList.xml'):
		tree = ET.ElementTree(self.top_element)
		tree.write(filename,encoding="utf-8",xml_declaration=True)

def read_AFCOffset_and_ZPosition_from_MAF_file(filename):
	tree = ET.parse(filename)
	root = tree.getroot()
	XYZStagePointDefinition = root.find('XYZStagePointDefinition')
	AFCOffset = float(XYZStagePointDefinition.get('AFCOffset'))
	AdditionalZPositionList = XYZStagePointDefinition.find('AdditionalZPositionList')
	AdditionalZPosition  = AdditionalZPositionList.find('AdditionalZPosition')
	ZPosition = float(AdditionalZPosition.get('ZPosition'))
	return AFCOffset,ZPosition

def read_StageXYPos(filename):
	tree = ET.parse(filename)
	root = tree.getroot()
	XYZStagePointDefinition = root.find('XYZStagePointDefinition')
	StageXPos = float(XYZStagePointDefinition.get('StageXPos'))
	StageYPos = float(XYZStagePointDefinition.get('StageYPos'))
	return StageXPos,StageYPos