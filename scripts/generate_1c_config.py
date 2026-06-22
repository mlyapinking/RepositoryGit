#!/usr/bin/env python3
"""Generate full 1C configuration XML dump for car rental system."""

import hashlib
import re
import uuid
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "1c-config"
# Учебная версия 1С: 8.3.17 → формат выгрузки 2.10
VERSION = "2.10"
COMPATIBILITY_MODE = "Version8_3_17"
# Облегчённая сборка: без отчётов, предопределённых данных и тяжёлых прав
EDUCATIONAL_LITE = True

NS = (
    'xmlns="http://v8.1c.ru/8.3/MDClasses" '
    'xmlns:app="http://v8.1c.ru/8.2/managed-application/core" '
    'xmlns:cfg="http://v8.1c.ru/8.1/data/enterprise/current-config" '
    'xmlns:cmi="http://v8.1c.ru/8.2/managed-application/cmi" '
    'xmlns:ent="http://v8.1c.ru/8.1/data/enterprise" '
    'xmlns:lf="http://v8.1c.ru/8.2/managed-application/logform" '
    'xmlns:style="http://v8.1c.ru/8.1/data/ui/style" '
    'xmlns:sys="http://v8.1c.ru/8.1/data/ui/fonts/system" '
    'xmlns:v8="http://v8.1c.ru/8.1/data/core" '
    'xmlns:v8ui="http://v8.1c.ru/8.1/data/ui" '
    'xmlns:web="http://v8.1c.ru/8.1/data/ui/colors/web" '
    'xmlns:win="http://v8.1c.ru/8.1/data/ui/colors/windows" '
    'xmlns:xen="http://v8.1c.ru/8.3/xcf/enums" '
    'xmlns:xpr="http://v8.1c.ru/8.3/xcf/predef" '
    'xmlns:xr="http://v8.1c.ru/8.3/xcf/readable" '
    'xmlns:xs="http://www.w3.org/2001/XMLSchema" '
    'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"'
)

_uuids = {}


def uid(key: str) -> str:
    if key not in _uuids:
        _uuids[key] = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"car-rental-1c::{key}"))
    return _uuids[key]


def config_version(name: str) -> str:
    h = hashlib.md5(name.encode()).hexdigest()
    return h + "00000000"


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def downgrade_configuration(cfg_text: str) -> str:
    """Strip properties from newer platforms for 8.3.17 educational edition."""
    cfg_text = re.sub(r'version="2\.\d+"', f'version="{VERSION}"', cfg_text, count=1)
    cfg_text = cfg_text.replace("Version8_3_27", COMPATIBILITY_MODE)
    cfg_text = re.sub(
        r"<UsedMobileApplicationFunctionalities>.*?</UsedMobileApplicationFunctionalities>",
        "<UsedMobileApplicationFunctionalities/>",
        cfg_text,
        flags=re.DOTALL,
    )
    cfg_text = re.sub(
        r"\s*<xr:ContainedObject>\s*<xr:ClassId>9cd510cd-abfc-11d4-9434-004095e12fc7</xr:ClassId>\s*"
        r"<xr:ObjectId>b8ba0334-844c-44ad-8069-50de0a73125a</xr:ObjectId>\s*</xr:ContainedObject>\s*",
        "\n",
        cfg_text,
        flags=re.DOTALL,
    )
    if EDUCATIONAL_LITE:
        cfg_text = re.sub(r"\s*<Report>[^<]+</Report>\s*", "\n", cfg_text)
        cfg_text = re.sub(r"\s*<Role>Менеджер</Role>\s*", "\n", cfg_text)
        cfg_text = re.sub(r"\s*<Role>ВсеПрава</Role>\s*", "\n", cfg_text)
        cfg_text = cfg_text.replace(
            "<DefaultRoles>\n\t\t\t\t<xr:Item xsi:type=\"xr:MDObjectRef\">Role.Администратор</xr:Item>\n"
            "\t\t\t\t<xr:Item xsi:type=\"xr:MDObjectRef\">Role.ВсеПрава</xr:Item>\n"
            "\t\t\t</DefaultRoles>",
            "<DefaultRoles>\n\t\t\t\t<xr:Item xsi:type=\"xr:MDObjectRef\">Role.Администратор</xr:Item>\n"
            "\t\t\t</DefaultRoles>",
        )
    newer_mobile = [
        "SpeechToText", "Geofences", "IncomingShareRequests",
        "AllIncomingShareRequestsTypesProcessing", "DocumentScanning",
        "TextToSpeech", "AllFilesAccess", "Videoconferences", "NFC",
        "BackgroundAudioRecording", "ApplicationUsageStatistics", "BarcodeScanning",
    ]
    for tag in newer_mobile:
        cfg_text = re.sub(
            rf"\s*<app:functionality>\s*<app:functionality>{tag}</app:functionality>.*?</app:functionality>\s*",
            "",
            cfg_text,
            flags=re.DOTALL,
        )
    for tag in [
        "StandaloneConfigurationRestrictionRoles",
        "MobileApplicationURLs",
        "AllowedIncomingShareRequestTypes",
        "DefaultCollaborationSystemUsersChoiceForm",
        "DatabaseTablespacesUseMode",
    ]:
        cfg_text = re.sub(rf"\s*<{tag}/>\s*", "\n", cfg_text)
        cfg_text = re.sub(rf"\s*<{tag}>.*?</{tag}>\s*", "\n", cfg_text, flags=re.DOTALL)
    return cfg_text


def filter_config_dump_info(dump_text: str) -> str:
    """Keep only metadata entries that exist in the lite export."""
    if not EDUCATIONAL_LITE:
        return dump_text
    skip_prefixes = ("Report.", "Role.ВсеПрава", "Role.Менеджер", "Document.ФактПроката.Form.")
    lines = []
    for line in dump_text.splitlines():
        if '<Metadata name="' in line:
            name = line.split('name="', 1)[1].split('"', 1)[0]
            if any(name.startswith(p) for p in skip_prefixes):
                continue
        lines.append(line)
    return "\n".join(lines) + "\n"


def simple_rights() -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<Rights xmlns="http://v8.1c.ru/8.2/roles" xmlns:xs="http://www.w3.org/2001/XMLSchema" '
        f'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:type="Rights" version="{VERSION}">\n'
        "\t<setForNewObjects>true</setForNewObjects>\n"
        "\t<setForAttributesByDefault>true</setForAttributesByDefault>\n"
        "\t<independentRightsOfChildObjects>false</independentRightsOfChildObjects>\n"
        "</Rights>\n"
    )


def enum_predefined_ref(value: str) -> str:
    if ".EnumValue." in value:
        return value
    parts = value.split(".")
    if len(parts) == 3 and parts[0] == "Enum":
        return f"Enum.{parts[1]}.EnumValue.{parts[2]}"
    return value


def header() -> str:
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<MetaDataObject {NS} version="{VERSION}">\n'


def footer() -> str:
    return "</MetaDataObject>\n"


def synonym(text: str, indent: str = "\t\t\t") -> str:
  return (
      f"{indent}<Synonym>\n"
      f"{indent}\t<v8:item>\n"
      f"{indent}\t\t<v8:lang>ru</v8:lang>\n"
      f"{indent}\t\t<v8:content>{text}</v8:content>\n"
      f"{indent}\t</v8:item>\n"
      f"{indent}</Synonym>"
  )


def std_attr(name: str) -> str:
    return f"""				<xr:StandardAttribute name="{name}">
					<xr:LinkByType/>
					<xr:FillChecking>DontCheck</xr:FillChecking>
					<xr:MultiLine>false</xr:MultiLine>
					<xr:FillFromFillingValue>false</xr:FillFromFillingValue>
					<xr:CreateOnInput>Auto</xr:CreateOnInput>
					<xr:MaxValue xsi:nil="true"/>
					<xr:ToolTip/>
					<xr:ExtendedEdit>false</xr:ExtendedEdit>
					<xr:Format/>
					<xr:ChoiceForm/>
					<xr:QuickChoice>Auto</xr:QuickChoice>
					<xr:ChoiceHistoryOnInput>Auto</xr:ChoiceHistoryOnInput>
					<xr:EditFormat/>
					<xr:PasswordMode>false</xr:PasswordMode>
					<xr:DataHistory>Use</xr:DataHistory>
					<xr:MarkNegatives>false</xr:MarkNegatives>
					<xr:MinValue xsi:nil="true"/>
					<xr:Synonym/>
					<xr:Comment/>
					<xr:FullTextSearch>Use</xr:FullTextSearch>
					<xr:ChoiceParameterLinks/>
					<xr:FillValue xsi:nil="true"/>
					<xr:Mask/>
					<xr:ChoiceParameters/>
				</xr:StandardAttribute>"""


def catalog_std_attrs() -> str:
    names = [
        "PredefinedDataName", "Predefined", "Ref", "DeletionMark", "IsFolder",
        "Owner", "Parent", "Description", "Code",
    ]
    return "\n".join(std_attr(n) for n in names)


def document_std_attrs() -> str:
    return "\n".join(std_attr(n) for n in ["Posted", "Ref", "DeletionMark", "Date", "Number"])


def enum_std_attrs() -> str:
    return "\n".join(std_attr(n) for n in ["Order", "Ref"])


def register_std_attrs() -> str:
    return "\n".join(std_attr(n) for n in ["Active", "LineNumber", "Recorder", "Period"])


def attr_block(name: str, synonym_text: str, type_xml: str, attr_uuid: str, fill_check="DontCheck") -> str:
    return f"""			<Attribute uuid="{attr_uuid}">
				<Properties>
					<Name>{name}</Name>
					{synonym(synonym_text, "\t\t\t\t")}
					<Comment/>
					<Type>
{type_xml}
					</Type>
					<PasswordMode>false</PasswordMode>
					<Format/>
					<EditFormat/>
					<ToolTip/>
					<MarkNegatives>false</MarkNegatives>
					<Mask/>
					<MultiLine>false</MultiLine>
					<ExtendedEdit>false</ExtendedEdit>
					<MinValue xsi:nil="true"/>
					<MaxValue xsi:nil="true"/>
					<FillFromFillingValue>false</FillFromFillingValue>
					<FillValue xsi:nil="true"/>
					<FillChecking>{fill_check}</FillChecking>
					<ChoiceFoldersAndItems>Items</ChoiceFoldersAndItems>
					<ChoiceParameterLinks/>
					<ChoiceParameters/>
					<QuickChoice>Auto</QuickChoice>
					<CreateOnInput>Auto</CreateOnInput>
					<ChoiceForm/>
					<LinkByType/>
					<ChoiceHistoryOnInput>Auto</ChoiceHistoryOnInput>
					<Indexing>DontIndex</Indexing>
					<FullTextSearch>Use</FullTextSearch>
					<DataHistory>Use</DataHistory>
				</Properties>
			</Attribute>"""


def type_string(length: int = 100) -> str:
    return (
        f"\t\t\t\t\t<v8:Type>xs:string</v8:Type>\n"
        f"\t\t\t\t\t<v8:StringQualifiers>\n"
        f"\t\t\t\t\t\t<v8:Length>{length}</v8:Length>\n"
        f"\t\t\t\t\t\t<v8:AllowedLength>Variable</v8:AllowedLength>\n"
        f"\t\t\t\t\t</v8:StringQualifiers>"
    )


def type_number(digits=15, frac=2, sign="Any") -> str:
    return (
        f"\t\t\t\t\t<v8:Type>xs:decimal</v8:Type>\n"
        f"\t\t\t\t\t<v8:NumberQualifiers>\n"
        f"\t\t\t\t\t\t<v8:Digits>{digits}</v8:Digits>\n"
        f"\t\t\t\t\t\t<v8:FractionDigits>{frac}</v8:FractionDigits>\n"
        f"\t\t\t\t\t\t<v8:AllowedSign>{sign}</v8:AllowedSign>\n"
        f"\t\t\t\t\t</v8:NumberQualifiers>"
    )


def type_date(fractions="Date") -> str:
    return (
        f"\t\t\t\t\t<v8:Type>xs:dateTime</v8:Type>\n"
        f"\t\t\t\t\t<v8:DateQualifiers>\n"
        f"\t\t\t\t\t\t<v8:DateFractions>{fractions}</v8:DateFractions>\n"
        f"\t\t\t\t\t</v8:DateQualifiers>"
    )


def type_ref(ref_type: str) -> str:
    return f"\t\t\t\t\t<v8:Type>cfg:{ref_type}</v8:Type>"


def catalog_generated(name: str) -> str:
    cats = ["Object", "Ref", "Selection", "List", "Manager"]
    lines = []
    for cat in cats:
        t = uid(f"gt:Catalog{cat}:{name}")
        v = uid(f"gv:Catalog{cat}:{name}")
        lines.append(
            f"\t\t\t<xr:GeneratedType name=\"Catalog{cat}.{name}\" category=\"{cat}\">\n"
            f"\t\t\t\t<xr:TypeId>{t}</xr:TypeId>\n"
            f"\t\t\t\t<xr:ValueId>{v}</xr:ValueId>\n"
            f"\t\t\t</xr:GeneratedType>"
        )
    return "\n".join(lines)


def document_generated(name: str) -> str:
    cats = ["Object", "Ref", "Selection", "List", "Manager"]
    lines = []
    for cat in cats:
        t = uid(f"gt:Document{cat}:{name}")
        v = uid(f"gv:Document{cat}:{name}")
        lines.append(
            f"\t\t\t<xr:GeneratedType name=\"Document{cat}.{name}\" category=\"{cat}\">\n"
            f"\t\t\t\t<xr:TypeId>{t}</xr:TypeId>\n"
            f"\t\t\t\t<xr:ValueId>{v}</xr:ValueId>\n"
            f"\t\t\t</xr:GeneratedType>"
        )
    return "\n".join(lines)


def enum_generated(name: str) -> str:
    cats = ["Ref", "Manager", "List"]
    lines = []
    for cat in cats:
        t = uid(f"gt:Enum{cat}:{name}")
        v = uid(f"gv:Enum{cat}:{name}")
        lines.append(
            f"\t\t\t<xr:GeneratedType name=\"Enum{cat}.{name}\" category=\"{cat}\">\n"
            f"\t\t\t\t<xr:TypeId>{t}</xr:TypeId>\n"
            f"\t\t\t\t<xr:ValueId>{v}</xr:ValueId>\n"
            f"\t\t\t</xr:GeneratedType>"
        )
    return "\n".join(lines)


def info_register_generated(name: str) -> str:
    cats = ["Record", "Manager", "Selection", "List", "RecordSet", "RecordKey", "RecordManager"]
    lines = []
    for cat in cats:
        t = uid(f"gt:IR{cat}:{name}")
        v = uid(f"gv:IR{cat}:{name}")
        lines.append(
            f"\t\t\t<xr:GeneratedType name=\"InformationRegister{cat}.{name}\" category=\"{cat}\">\n"
            f"\t\t\t\t<xr:TypeId>{t}</xr:TypeId>\n"
            f"\t\t\t\t<xr:ValueId>{v}</xr:ValueId>\n"
            f"\t\t\t</xr:GeneratedType>"
        )
    return "\n".join(lines)


def accum_register_generated(name: str) -> str:
    cats = ["Record", "Manager", "Selection", "List", "RecordSet", "RecordKey"]
    lines = []
    for cat in cats:
        t = uid(f"gt:AR{cat}:{name}")
        v = uid(f"gv:AR{cat}:{name}")
        lines.append(
            f"\t\t\t<xr:GeneratedType name=\"AccumulationRegister{cat}.{name}\" category=\"{cat}\">\n"
            f"\t\t\t\t<xr:TypeId>{t}</xr:TypeId>\n"
            f"\t\t\t\t<xr:ValueId>{v}</xr:ValueId>\n"
            f"\t\t\t</xr:GeneratedType>"
        )
    return "\n".join(lines)


def report_generated(name: str) -> str:
    t = uid(f"gt:ReportObject:{name}")
    v = uid(f"gv:ReportObject:{name}")
    t2 = uid(f"gt:ReportManager:{name}")
    v2 = uid(f"gv:ReportManager:{name}")
    return (
        f"\t\t\t<xr:GeneratedType name=\"ReportObject.{name}\" category=\"Object\">\n"
        f"\t\t\t\t<xr:TypeId>{t}</xr:TypeId>\n"
        f"\t\t\t\t<xr:ValueId>{v}</xr:ValueId>\n"
        f"\t\t\t</xr:GeneratedType>\n"
        f"\t\t\t<xr:GeneratedType name=\"ReportManager.{name}\" category=\"Manager\">\n"
        f"\t\t\t\t<xr:TypeId>{t2}</xr:TypeId>\n"
        f"\t\t\t\t<xr:ValueId>{v2}</xr:ValueId>\n"
        f"\t\t\t</xr:GeneratedType>"
    )


def _reg_field_common(name: str, synonym_text: str, type_xml: str, obj_uuid: str, kind: str, extra: str) -> str:
    return f"""			<{kind} uuid="{obj_uuid}">
				<Properties>
					<Name>{name}</Name>
					{synonym(synonym_text, "\t\t\t\t")}
					<Comment/>
					<Type>
{type_xml}
					</Type>
					<PasswordMode>false</PasswordMode>
					<Format/>
					<EditFormat/>
					<ToolTip/>
					<MarkNegatives>false</MarkNegatives>
					<Mask/>
					<MultiLine>false</MultiLine>
					<ExtendedEdit>false</ExtendedEdit>
					<MinValue xsi:nil="true"/>
					<MaxValue xsi:nil="true"/>
					<FillChecking>DontCheck</FillChecking>
					<ChoiceFoldersAndItems>Items</ChoiceFoldersAndItems>
					<ChoiceParameterLinks/>
					<ChoiceParameters/>
					<QuickChoice>Auto</QuickChoice>
					<CreateOnInput>Auto</CreateOnInput>
					<ChoiceForm/>
					<LinkByType/>
					<ChoiceHistoryOnInput>Auto</ChoiceHistoryOnInput>
{extra}
				</Properties>
			</{kind}>"""


def info_reg_resource(name: str, synonym_text: str, type_xml: str, obj_uuid: str) -> str:
    extra = (
        "\t\t\t\t\t<FillFromFillingValue>false</FillFromFillingValue>\n"
        "\t\t\t\t\t<FillValue xsi:nil=\"true\"/>\n"
        "\t\t\t\t\t<Indexing>DontIndex</Indexing>\n"
        "\t\t\t\t\t<FullTextSearch>Use</FullTextSearch>\n"
        "\t\t\t\t\t<DataHistory>Use</DataHistory>"
    )
    return _reg_field_common(name, synonym_text, type_xml, obj_uuid, "Resource", extra)


def info_reg_dimension(name: str, synonym_text: str, type_xml: str, obj_uuid: str, master: bool = True) -> str:
    extra = (
        "\t\t\t\t\t<FillFromFillingValue>false</FillFromFillingValue>\n"
        "\t\t\t\t\t<FillValue xsi:nil=\"true\"/>\n"
        f"\t\t\t\t\t<Master>{str(master).lower()}</Master>\n"
        f"\t\t\t\t\t<MainFilter>{str(master).lower()}</MainFilter>\n"
        "\t\t\t\t\t<DenyIncompleteValues>false</DenyIncompleteValues>\n"
        "\t\t\t\t\t<Indexing>DontIndex</Indexing>\n"
        "\t\t\t\t\t<FullTextSearch>Use</FullTextSearch>\n"
        "\t\t\t\t\t<DataHistory>Use</DataHistory>"
    )
    return _reg_field_common(name, synonym_text, type_xml, obj_uuid, "Dimension", extra)


def accum_reg_resource(name: str, synonym_text: str, type_xml: str, obj_uuid: str) -> str:
    extra = "\t\t\t\t\t<FullTextSearch>Use</FullTextSearch>"
    return _reg_field_common(name, synonym_text, type_xml, obj_uuid, "Resource", extra)


def accum_reg_dimension(name: str, synonym_text: str, type_xml: str, obj_uuid: str) -> str:
    extra = (
        "\t\t\t\t\t<DenyIncompleteValues>false</DenyIncompleteValues>\n"
        "\t\t\t\t\t<Indexing>DontIndex</Indexing>\n"
        "\t\t\t\t\t<FullTextSearch>Use</FullTextSearch>\n"
        "\t\t\t\t\t<UseInTotals>true</UseInTotals>"
    )
    return _reg_field_common(name, synonym_text, type_xml, obj_uuid, "Dimension", extra)


def catalog(name: str, synonym_text: str, obj_uuid: str, attributes: list, forms: list | None = None) -> str:
    attrs_xml = "\n".join(
        attr_block(a["name"], a["synonym"], a["type"], a["uuid"], a.get("fill", "DontCheck"))
        for a in attributes
    )
    forms = forms if forms is not None else []
    forms_xml = "\n".join(f"\t\t\t<Form>{f}</Form>" for f in forms)
    default_obj = f"Catalog.{name}.Form.{forms[0]}" if forms else ""
    default_list = f"Catalog.{name}.Form.{forms[1]}" if len(forms) > 1 else ""
    return (
        header()
        + f'\t<Catalog uuid="{obj_uuid}">\n'
        + "\t\t<InternalInfo>\n"
        + catalog_generated(name)
        + "\n\t\t</InternalInfo>\n"
        + "\t\t<Properties>\n"
        + f"\t\t\t<Name>{name}</Name>\n"
        + f"\t\t\t{synonym(synonym_text)}\n"
        + "\t\t\t<Comment/>\n"
        + "\t\t\t<Hierarchical>false</Hierarchical>\n"
        + "\t\t\t<HierarchyType>HierarchyFoldersAndItems</HierarchyType>\n"
        + "\t\t\t<LimitLevelCount>false</LimitLevelCount>\n"
        + "\t\t\t<LevelCount>2</LevelCount>\n"
        + "\t\t\t<FoldersOnTop>true</FoldersOnTop>\n"
        + "\t\t\t<UseStandardCommands>true</UseStandardCommands>\n"
        + "\t\t\t<Owners/>\n"
        + "\t\t\t<SubordinationUse>ToItems</SubordinationUse>\n"
        + "\t\t\t<CodeLength>9</CodeLength>\n"
        + "\t\t\t<DescriptionLength>150</DescriptionLength>\n"
        + "\t\t\t<CodeType>String</CodeType>\n"
        + "\t\t\t<CodeAllowedLength>Variable</CodeAllowedLength>\n"
        + "\t\t\t<CodeSeries>WholeCatalog</CodeSeries>\n"
        + "\t\t\t<CheckUnique>true</CheckUnique>\n"
        + "\t\t\t<Autonumbering>true</Autonumbering>\n"
        + "\t\t\t<DefaultPresentation>AsDescription</DefaultPresentation>\n"
        + "\t\t\t<StandardAttributes>\n"
        + catalog_std_attrs()
        + "\n\t\t\t</StandardAttributes>\n"
        + "\t\t\t<Characteristics/>\n"
        + f"\t\t\t<PredefinedDataUpdate>{'DontAutoUpdate' if EDUCATIONAL_LITE else 'Auto'}</PredefinedDataUpdate>\n"
        + "\t\t\t<EditType>InDialog</EditType>\n"
        + "\t\t\t<QuickChoice>false</QuickChoice>\n"
        + "\t\t\t<ChoiceMode>BothWays</ChoiceMode>\n"
        + f"\t\t\t<InputByString>\n\t\t\t\t<xr:Field>Catalog.{name}.StandardAttribute.Description</xr:Field>\n\t\t\t\t<xr:Field>Catalog.{name}.StandardAttribute.Code</xr:Field>\n\t\t\t</InputByString>\n"
        + "\t\t\t<SearchStringModeOnInputByString>Begin</SearchStringModeOnInputByString>\n"
        + "\t\t\t<FullTextSearchOnInputByString>DontUse</FullTextSearchOnInputByString>\n"
        + "\t\t\t<ChoiceDataGetModeOnInputByString>Directly</ChoiceDataGetModeOnInputByString>\n"
        + (f"\t\t\t<DefaultObjectForm>{default_obj}</DefaultObjectForm>\n" if default_obj else "\t\t\t<DefaultObjectForm/>\n")
        + "\t\t\t<DefaultFolderForm/>\n"
        + (f"\t\t\t<DefaultListForm>{default_list}</DefaultListForm>\n" if default_list else "\t\t\t<DefaultListForm/>\n")
        + "\t\t\t<DefaultChoiceForm/>\n"
        + "\t\t\t<DefaultFolderChoiceForm/>\n"
        + "\t\t\t<AuxiliaryObjectForm/>\n"
        + "\t\t\t<AuxiliaryFolderForm/>\n"
        + "\t\t\t<AuxiliaryListForm/>\n"
        + "\t\t\t<AuxiliaryChoiceForm/>\n"
        + "\t\t\t<AuxiliaryFolderChoiceForm/>\n"
        + "\t\t\t<IncludeHelpInContents>false</IncludeHelpInContents>\n"
        + "\t\t\t<BasedOn/>\n"
        + "\t\t\t<DataLockFields/>\n"
        + "\t\t\t<DataLockControlMode>Managed</DataLockControlMode>\n"
        + "\t\t\t<FullTextSearch>Use</FullTextSearch>\n"
        + f"\t\t\t<ObjectPresentation>\n\t\t\t\t<v8:item><v8:lang>ru</v8:lang><v8:content>{synonym_text}</v8:content></v8:item>\n\t\t\t</ObjectPresentation>\n"
        + "\t\t\t<ExtendedObjectPresentation/>\n"
        + f"\t\t\t<ListPresentation>\n\t\t\t\t<v8:item><v8:lang>ru</v8:lang><v8:content>{synonym_text}</v8:content></v8:item>\n\t\t\t</ListPresentation>\n"
        + "\t\t\t<ExtendedListPresentation/>\n"
        + "\t\t\t<Explanation/>\n"
        + "\t\t\t<CreateOnInput>Use</CreateOnInput>\n"
        + "\t\t\t<ChoiceHistoryOnInput>Auto</ChoiceHistoryOnInput>\n"
        + "\t\t\t<DataHistory>DontUse</DataHistory>\n"
        + "\t\t\t<UpdateDataHistoryImmediatelyAfterWrite>false</UpdateDataHistoryImmediatelyAfterWrite>\n"
        + "\t\t\t<ExecuteAfterWriteDataHistoryVersionProcessing>false</ExecuteAfterWriteDataHistoryVersionProcessing>\n"
        + "\t\t\t</Properties>\n"
        + "\t\t<ChildObjects>\n"
        + attrs_xml
        + "\n"
        + forms_xml
        + "\n\t\t</ChildObjects>\n"
        + "\t</Catalog>\n"
        + footer()
    )


def document(name: str, synonym_text: str, obj_uuid: str, attributes: list, register_records: list | None = None, forms: list | None = None) -> str:
    attrs_xml = "\n".join(
        attr_block(a["name"], a["synonym"], a["type"], a["uuid"], a.get("fill", "DontCheck"))
        for a in attributes
    )
    forms = forms or []
    forms_xml = "\n".join(f"\t\t\t<Form>{f}</Form>" for f in forms)
    reg_xml = ""
    if register_records:
        reg_xml = "\n\t\t\t<RegisterRecords>\n" + "\n".join(
            f'\t\t\t\t<xr:Item xsi:type="xr:MDObjectRef">{r}</xr:Item>' for r in register_records
        ) + "\n\t\t\t</RegisterRecords>"
    default_form = f"Document.{name}.Form.{forms[0]}" if forms else ""
    return (
        header()
        + f'\t<Document uuid="{obj_uuid}">\n'
        + "\t\t<InternalInfo>\n"
        + document_generated(name)
        + "\n\t\t</InternalInfo>\n"
        + "\t\t<Properties>\n"
        + f"\t\t\t<Name>{name}</Name>\n"
        + f"\t\t\t{synonym(synonym_text)}\n"
        + "\t\t\t<Comment/>\n"
        + "\t\t\t<UseStandardCommands>true</UseStandardCommands>\n"
        + "\t\t\t<Numerator/>\n"
        + "\t\t\t<NumberType>String</NumberType>\n"
        + "\t\t\t<NumberLength>11</NumberLength>\n"
        + "\t\t\t<NumberAllowedLength>Variable</NumberAllowedLength>\n"
        + "\t\t\t<NumberPeriodicity>Year</NumberPeriodicity>\n"
        + "\t\t\t<CheckUnique>true</CheckUnique>\n"
        + "\t\t\t<Autonumbering>true</Autonumbering>\n"
        + "\t\t\t<StandardAttributes>\n"
        + document_std_attrs()
        + "\n\t\t\t</StandardAttributes>\n"
        + "\t\t\t<Characteristics/>\n"
        + "\t\t\t<BasedOn/>\n"
        + f"\t\t\t<InputByString>\n\t\t\t\t<xr:Field>Document.{name}.StandardAttribute.Number</xr:Field>\n\t\t\t</InputByString>\n"
        + "\t\t\t<CreateOnInput>DontUse</CreateOnInput>\n"
        + "\t\t\t<SearchStringModeOnInputByString>Begin</SearchStringModeOnInputByString>\n"
        + "\t\t\t<FullTextSearchOnInputByString>DontUse</FullTextSearchOnInputByString>\n"
        + "\t\t\t<ChoiceDataGetModeOnInputByString>Directly</ChoiceDataGetModeOnInputByString>\n"
        + (f"\t\t\t<DefaultObjectForm>{default_form}</DefaultObjectForm>\n" if default_form else "\t\t\t<DefaultObjectForm/>\n")
        + "\t\t\t<DefaultListForm/>\n"
        + "\t\t\t<DefaultChoiceForm/>\n"
        + "\t\t\t<AuxiliaryObjectForm/>\n"
        + "\t\t\t<AuxiliaryListForm/>\n"
        + "\t\t\t<AuxiliaryChoiceForm/>\n"
        + "\t\t\t<Posting>Allow</Posting>\n"
        + "\t\t\t<RealTimePosting>Allow</RealTimePosting>\n"
        + "\t\t\t<RegisterRecordsDeletion>AutoDeleteOnUnpost</RegisterRecordsDeletion>\n"
        + "\t\t\t<RegisterRecordsWritingOnPost>WriteSelected</RegisterRecordsWritingOnPost>\n"
        + "\t\t\t<SequenceFilling>AutoFill</SequenceFilling>\n"
        + reg_xml
        + "\n\t\t\t<PostInPrivilegedMode>true</PostInPrivilegedMode>\n"
        + "\t\t\t<UnpostInPrivilegedMode>true</UnpostInPrivilegedMode>\n"
        + "\t\t\t<IncludeHelpInContents>false</IncludeHelpInContents>\n"
        + "\t\t\t<DataLockFields/>\n"
        + "\t\t\t<DataLockControlMode>Managed</DataLockControlMode>\n"
        + "\t\t\t<FullTextSearch>Use</FullTextSearch>\n"
        + f"\t\t\t<ObjectPresentation>\n\t\t\t\t<v8:item><v8:lang>ru</v8:lang><v8:content>{synonym_text}</v8:content></v8:item>\n\t\t\t</ObjectPresentation>\n"
        + "\t\t\t<ExtendedObjectPresentation/>\n"
        + f"\t\t\t<ListPresentation>\n\t\t\t\t<v8:item><v8:lang>ru</v8:lang><v8:content>{synonym_text}</v8:content></v8:item>\n\t\t\t</ListPresentation>\n"
        + "\t\t\t<ExtendedListPresentation/>\n"
        + "\t\t\t<Explanation/>\n"
        + "\t\t\t<ChoiceHistoryOnInput>Auto</ChoiceHistoryOnInput>\n"
        + "\t\t\t<DataHistory>DontUse</DataHistory>\n"
        + "\t\t\t<UpdateDataHistoryImmediatelyAfterWrite>false</UpdateDataHistoryImmediatelyAfterWrite>\n"
        + "\t\t\t<ExecuteAfterWriteDataHistoryVersionProcessing>false</ExecuteAfterWriteDataHistoryVersionProcessing>\n"
        + "\t\t\t</Properties>\n"
        + "\t\t<ChildObjects>\n"
        + attrs_xml
        + ("\n" + forms_xml if forms_xml else "")
        + "\n\t\t</ChildObjects>\n"
        + "\t</Document>\n"
        + footer()
    )


def enum_obj(name: str, synonym_text: str, obj_uuid: str, values: list) -> str:
    vals_xml = []
    for v in values:
        vals_xml.append(
            f"""\t\t\t<EnumValue uuid="{v['uuid']}">
\t\t\t\t<Properties>
\t\t\t\t\t<Name>{v['name']}</Name>
\t\t\t\t\t{synonym(v['synonym'], "\t\t\t\t\t")}
\t\t\t\t\t<Comment/>
\t\t\t\t</Properties>
\t\t\t</EnumValue>"""
        )
    return (
        header()
        + f'\t<Enum uuid="{obj_uuid}">\n'
        + "\t\t<InternalInfo>\n"
        + enum_generated(name)
        + "\n\t\t</InternalInfo>\n"
        + "\t\t<Properties>\n"
        + f"\t\t\t<Name>{name}</Name>\n"
        + f"\t\t\t{synonym(synonym_text)}\n"
        + "\t\t\t<Comment/>\n"
        + "\t\t\t<UseStandardCommands>false</UseStandardCommands>\n"
        + "\t\t\t<StandardAttributes>\n"
        + enum_std_attrs()
        + "\n\t\t\t</StandardAttributes>\n"
        + "\t\t\t<Characteristics/>\n"
        + "\t\t\t<QuickChoice>true</QuickChoice>\n"
        + "\t\t\t<ChoiceMode>BothWays</ChoiceMode>\n"
        + "\t\t\t<DefaultListForm/>\n"
        + "\t\t\t<DefaultChoiceForm/>\n"
        + "\t\t\t<AuxiliaryListForm/>\n"
        + "\t\t\t<AuxiliaryChoiceForm/>\n"
        + "\t\t\t<ListPresentation/>\n"
        + "\t\t\t<ExtendedListPresentation/>\n"
        + "\t\t\t<Explanation/>\n"
        + "\t\t\t<ChoiceHistoryOnInput>Auto</ChoiceHistoryOnInput>\n"
        + "\t\t\t</Properties>\n"
        + "\t\t<ChildObjects>\n"
        + "\n".join(vals_xml)
        + "\n\t\t</ChildObjects>\n"
        + "\t</Enum>\n"
        + footer()
    )


def subsystem(name: str, synonym_text: str, obj_uuid: str, content: list, picture: str = "") -> str:
    content_xml = "\n".join(
        f'\t\t\t\t<xr:Item xsi:type="xr:MDObjectRef">{c}</xr:Item>' for c in content
    )
    picture_xml = "<Picture/>"
    if picture:
        picture_xml = (
            f"<Picture>\n"
            f"\t\t\t\t<xr:Ref>CommonPicture.{picture}</xr:Ref>\n"
            f"\t\t\t\t<xr:LoadTransparent>true</xr:LoadTransparent>\n"
            f"\t\t\t</Picture>"
        )
    return (
        header()
        + f'\t<Subsystem uuid="{obj_uuid}">\n'
        + "\t\t<Properties>\n"
        + f"\t\t\t<Name>{name}</Name>\n"
        + f"\t\t\t{synonym(synonym_text)}\n"
        + "\t\t\t<Comment/>\n"
        + "\t\t\t<IncludeHelpInContents>true</IncludeHelpInContents>\n"
        + "\t\t\t<IncludeInCommandInterface>true</IncludeInCommandInterface>\n"
        + "\t\t\t<UseOneCommand>false</UseOneCommand>\n"
        + "\t\t\t<Explanation/>\n"
        + f"\t\t\t{picture_xml}\n"
        + "\t\t\t<Content>\n"
        + content_xml
        + "\n\t\t\t</Content>\n"
        + "\t\t</Properties>\n"
        + "\t\t<ChildObjects/>\n"
        + "\t</Subsystem>\n"
        + footer()
    )


def role(name: str, synonym_text: str, obj_uuid: str) -> str:
    return (
        header()
        + f'\t<Role uuid="{obj_uuid}">\n'
        + "\t\t<Properties>\n"
        + f"\t\t\t<Name>{name}</Name>\n"
        + f"\t\t\t{synonym(synonym_text)}\n"
        + "\t\t\t<Comment/>\n"
        + "\t\t</Properties>\n"
        + "\t</Role>\n"
        + footer()
    )


def rights_all_objects() -> str:
    objects = [
        "Configuration.Конфигурация",
        "Subsystem.УчетАвтомобилей", "Subsystem.УчётКлиентов", "Subsystem.Прокат", "Subsystem.Справочники",
        "Catalog.Автомобили", "Catalog.Клиенты", "Catalog.Тарифы",
        "Document.ДоговАренды", "Document.ФактПроката",
        "Enum.ТипКоробкиПередач", "Enum.ТипТоплива", "Enum.СтатусыАвтомобиля",
        "Report.ДоходыОтПроката", "Report.СостояниеАвтопарка", "Report.ИсторияАвтомобилей",
        "InformationRegister.ЦеныПроката", "InformationRegister.СтатусыАвтомобилей",
        "AccumulationRegister.АрендаОбороты", "AccumulationRegister.ВзаиморасчетыСКлиентами",
    ]
    rights = ["Read", "View", "Insert", "Update", "Delete", "Posting", "UndoPosting", "InteractiveInsert",
              "Edit", "InteractiveSetDeletionMark", "InteractiveClearDeletionMark", "InteractivePosting",
              "InteractivePostingRegular", "InteractiveUndoPosting", "InteractiveActivate", "InteractiveDeactivate",
              "Output", "Use", "ViewDataHistory", "EditDataHistoryVersion", "SwitchToDataHistoryVersion"]
    blocks = []
    for obj in objects:
        rs = "\n".join(f"\t\t\t<right><name>{r}</name><value>true</value></right>" for r in rights)
        blocks.append(f"\t<object>\n\t\t<name>{obj}</name>\n{rs}\n\t</object>")
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<Rights xmlns="http://v8.1c.ru/8.2/roles" xmlns:xs="http://www.w3.org/2001/XMLSchema" '
        f'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:type="Rights" version="{VERSION}">\n'
        "\t<setForNewObjects>true</setForNewObjects>\n"
        "\t<setForAttributesByDefault>true</setForAttributesByDefault>\n"
        "\t<independentRightsOfChildObjects>false</independentRightsOfChildObjects>\n"
        + "\n".join(blocks)
        + "\n</Rights>\n"
    )


def manager_rights(objects: list) -> str:
    rights = ["Read", "View", "Insert", "Update", "Posting", "UndoPosting", "InteractiveInsert", "Edit",
              "InteractivePosting", "InteractiveUndoPosting", "Output", "Use"]
    blocks = []
    for obj in objects:
        rs = "\n".join(f"\t\t\t<right><name>{r}</name><value>true</value></right>" for r in rights)
        blocks.append(f"\t<object>\n\t\t<name>{obj}</name>\n{rs}\n\t</object>")
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<Rights xmlns="http://v8.1c.ru/8.2/roles" xmlns:xs="http://www.w3.org/2001/XMLSchema" '
        f'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:type="Rights" version="{VERSION}">\n'
        "\t<setForNewObjects>false</setForNewObjects>\n"
        "\t<setForAttributesByDefault>true</setForAttributesByDefault>\n"
        "\t<independentRightsOfChildObjects>false</independentRightsOfChildObjects>\n"
        + "\n".join(blocks)
        + "\n</Rights>\n"
    )


def predefined_catalog(items: list) -> str:
    rows = []
    for item in items:
        attrs = ""
        for k, v in item.get("attrs", {}).items():
            if v.startswith("Enum."):
                ref = enum_predefined_ref(v)
                attrs += f'\n\t\t\t<{k} xsi:type="xr:DesignTimeRef">{ref}</{k}>'
            elif len(v) == 10 and v[4] == "-" and v[7] == "-":
                attrs += f'\n\t\t\t<{k} xsi:type="xs:dateTime">{v}T00:00:00</{k}>'
            else:
                attrs += f"\n\t\t\t<{k}>{v}</{k}>"
        item_id = item.get("uuid") or uid(f"predef:{item['name']}")
        rows.append(
            f"""\t\t<Item id="{item_id}">
\t\t\t<Name>{item['name']}</Name>
\t\t\t<Code>{item['code']}</Code>
\t\t\t<Description>{item['description']}</Description>
\t\t\t<IsFolder>false</IsFolder>{attrs}
\t\t</Item>"""
        )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<PredefinedData xmlns="http://v8.1c.ru/8.3/xcf/predef" '
        'xmlns:v8="http://v8.1c.ru/8.1/data/core" '
        'xmlns:xr="http://v8.1c.ru/8.3/xcf/readable" '
        'xmlns:xs="http://www.w3.org/2001/XMLSchema" '
        'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
        f'xsi:type="CatalogPredefinedItems" version="{VERSION}">\n'
        + "\n".join(rows)
        + "\n</PredefinedData>\n"
    )


def catalog_form_meta(catalog_name: str, form_name: str, form_uuid: str) -> str:
    return (
        header()
        + f'\t<Form uuid="{form_uuid}">\n'
        + "\t\t<Properties>\n"
        + f"\t\t\t<Name>{form_name}</Name>\n"
        + f"\t\t\t{synonym(form_name)}\n"
        + "\t\t\t<Comment/>\n"
        + "\t\t\t<FormType>Managed</FormType>\n"
        + "\t\t\t<IncludeHelpInContents>false</IncludeHelpInContents>\n"
        + "\t\t\t<UsePurposes>\n"
        + "\t\t\t\t<v8:Value xsi:type=\"app:ApplicationUsePurpose\">PlatformApplication</v8:Value>\n"
        + "\t\t\t</UsePurposes>\n"
        + "\t\t</Properties>\n"
        + "\t</Form>\n"
        + footer()
    )


def catalog_item_form(catalog_name: str, fields: list) -> str:
    items = []
    y = 0
    for field in fields:
        y += 1
        items.append(
            f"""\t\t<InputField name="{field}" id="{y}">
\t\t\t<DataPath>Объект.{field}</DataPath>
\t\t\t<ContextMenu name="{field}КонтекстноеМеню" id="{y}01"/>
\t\t\t<ExtendedTooltip name="{field}РасширеннаяПодсказка" id="{y}02"/>
\t\t</InputField>"""
        )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<Form xmlns="http://v8.1c.ru/8.3/xcf/logform" xmlns:app="http://v8.1c.ru/8.2/managed-application/core" '
        'xmlns:cfg="http://v8.1c.ru/8.1/data/enterprise/current-config" '
        'xmlns:v8="http://v8.1c.ru/8.1/data/core" xmlns:v8ui="http://v8.1c.ru/8.1/data/ui" '
        f'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" version="{VERSION}">\n'
        '\t<AutoCommandBar name="ФормаКоманднаяПанель" id="-1">\n'
        '\t\t<Autofill>true</Autofill>\n'
        '\t</AutoCommandBar>\n'
        '\t<ChildItems>\n'
        + "\n".join(items)
        + '\n\t</ChildItems>\n'
        f'\t<Attributes>\n\t\t<Attribute name="Объект" id="1">\n'
        f'\t\t\t<Type><v8:Type>cfg:CatalogObject.{catalog_name}</v8:Type></Type>\n'
        '\t\t\t<MainAttribute>true</MainAttribute>\n'
        '\t\t\t<SavedData>true</SavedData>\n'
        '\t\t</Attribute>\n\t</Attributes>\n</Form>\n'
    )


def document_form_meta(form_uuid: str) -> str:
    return (
        header()
        + f'\t<Form uuid="{form_uuid}">\n'
        + "\t\t<Properties>\n"
        + "\t\t\t<Name>ФормаДокумента</Name>\n"
        + synonym("Форма документа")
        + "\n\t\t\t<Comment/>\n"
        + "\t\t\t<FormType>Managed</FormType>\n"
        + "\t\t\t<IncludeHelpInContents>false</IncludeHelpInContents>\n"
        + "\t\t\t<UsePurposes>\n"
        + "\t\t\t\t<v8:Value xsi:type=\"app:ApplicationUsePurpose\">PlatformApplication</v8:Value>\n"
        + "\t\t\t</UsePurposes>\n"
        + "\t\t</Properties>\n"
        + "\t</Form>\n"
        + footer()
    )


def document_item_form(doc_name: str, fields: list) -> str:
    items = []
    y = 0
    for field in fields:
        y += 1
        items.append(
            f"""\t\t<InputField name="{field}" id="{y}">
\t\t\t<DataPath>Объект.{field}</DataPath>
\t\t\t<ContextMenu name="{field}КонтекстноеМеню" id="{y}01"/>
\t\t\t<ExtendedTooltip name="{field}РасширеннаяПодсказка" id="{y}02"/>
\t\t</InputField>"""
        )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<Form xmlns="http://v8.1c.ru/8.3/xcf/logform" xmlns:app="http://v8.1c.ru/8.2/managed-application/core" '
        'xmlns:cfg="http://v8.1c.ru/8.1/data/enterprise/current-config" '
        'xmlns:v8="http://v8.1c.ru/8.1/data/core" xmlns:v8ui="http://v8.1c.ru/8.1/data/ui" '
        f'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" version="{VERSION}">\n'
        '\t<AutoCommandBar name="ФормаКоманднаяПанель" id="-1">\n'
        '\t\t<Autofill>true</Autofill>\n'
        '\t</AutoCommandBar>\n'
        '\t<ChildItems>\n'
        + "\n".join(items)
        + '\n\t</ChildItems>\n'
        f'\t<Attributes>\n\t\t<Attribute name="Объект" id="1">\n'
        f'\t\t\t<Type><v8:Type>cfg:DocumentObject.{doc_name}</v8:Type></Type>\n'
        '\t\t\t<MainAttribute>true</MainAttribute>\n'
        '\t\t\t<SavedData>true</SavedData>\n'
        '\t\t</Attribute>\n\t</Attributes>\n</Form>\n'
    )


def object_module_posting() -> str:
    return """// Автоматическое движение по регистрам при проведении

Процедура ОбработкаПроведения(Отказ, РежимПроведения)

\t// Движения формируются платформой по настройке документа

КонецПроцедуры
"""


def main() -> None:
    if OUT.exists():
        import shutil
        shutil.rmtree(OUT)
    OUT.mkdir()

    # --- Catalogs ---
    auto_attrs = [
        {"name": "Марка", "synonym": "Марка", "uuid": "2ace88c4-debd-4ae1-91cf-d1778c45bc06", "type": type_string(50), "fill": "ShowError"},
        {"name": "Модель", "synonym": "Модель", "uuid": "26ca8280-440c-4a49-b9d4-1a5c08a4a5fd", "type": type_string(50), "fill": "ShowError"},
        {"name": "ГосНомер", "synonym": "Гос. номер", "uuid": "80b4e4af-945b-478b-9c8f-cb287d1cc815", "type": type_string(15), "fill": "ShowError"},
        {"name": "ГодВыпуска", "synonym": "Год выпуска", "uuid": "a29dd9f5-6e63-4fd2-ac41-6cc744910118", "type": type_number(4, 0, "Nonnegative")},
        {"name": "Цвет", "synonym": "Цвет", "uuid": "532628fd-dcd6-42a2-8e7f-82bd8ee4d32f", "type": type_string(30)},
        {"name": "ТипКоробкиПередач", "synonym": "Коробка передач", "uuid": "4a32b76e-c07c-4d9c-bc39-b80e6ef2623a", "type": type_ref("EnumRef.ТипКоробкиПередач")},
        {"name": "ТипТоплива", "synonym": "Тип топлива", "uuid": "5f534682-a290-4485-8cf3-dec7506ec240", "type": type_ref("EnumRef.ТипТоплива")},
        {"name": "ЦенаЗаСутки", "synonym": "Цена за сутки", "uuid": "5ff18e97-ad32-441b-864b-b66ab134c070", "type": type_number(15, 2, "Nonnegative")},
        {"name": "Статус", "synonym": "Статус", "uuid": "fd2bc21c-ef98-4f13-86f1-db1591972e6b", "type": type_ref("EnumRef.СтатусыАвтомобиля")},
    ]
    write(OUT / "Catalogs/Автомобили.xml", catalog("Автомобили", "Автомобили", "17914576-9cfb-4b53-b071-e64f40c0f4f3", auto_attrs))

    client_attrs = [
        {"name": "Телефон", "synonym": "Телефон", "uuid": "dc4e2317-5d94-4f1a-9ffc-b7329e086915", "type": type_string(20), "fill": "ShowError"},
        {"name": "Адрес", "synonym": "Адрес", "uuid": "2d91aa73-0800-4520-ab15-da3704989c28", "type": type_string(200)},
        {"name": "ДатаРождения", "synonym": "Дата рождения", "uuid": "f29ce6a2-2149-4948-b1da-b20d812197cc", "type": type_date("Date")},
        {"name": "НомерВУ", "synonym": "Номер ВУ", "uuid": "0ac763fd-b72e-4162-80e3-8805fb2ddbf4", "type": type_string(20), "fill": "ShowError"},
    ]
    write(OUT / "Catalogs/Клиенты.xml", catalog("Клиенты", "Клиенты", "b328ce6f-e3a7-4fa8-b3fe-b4b415bd5030", client_attrs))

    tariff_attrs = [
        {"name": "БазоваяСкорость", "synonym": "Базовая стоимость", "uuid": "95965eaa-9bd0-42a0-b4a0-0797ac936cf1", "type": type_number(15, 2, "Nonnegative"), "fill": "ShowError"},
        {"name": "ЛимитКм", "synonym": "Лимит км/сутки", "uuid": "8ea68b53-d5b2-4ece-b80f-dd5692031041", "type": type_number(10, 0, "Nonnegative")},
        {"name": "СтоимостьСверхлимита", "synonym": "Стоимость сверх лимита", "uuid": "64acc663-9ffd-4f29-b83a-96c6addae71f", "type": type_number(15, 2, "Nonnegative")},
    ]
    write(OUT / "Catalogs/Тарифы.xml", catalog("Тарифы", "Тарифы", "6cbffe2b-4012-4069-b652-8eb3f4563fae", tariff_attrs))

    if not EDUCATIONAL_LITE:
        # Predefined data (номенклатура справочников)
        write(OUT / "Catalogs/Автомобили/Ext/Predefined.xml", predefined_catalog([
            {"id": "1", "name": "ToyotaCamry", "code": "000000001", "description": "Toyota Camry А123ВС77",
             "attrs": {"Марка": "Toyota", "Модель": "Camry", "ГосНомер": "А123ВС77", "ГодВыпуска": "2022",
                       "Цвет": "Белый", "ТипКоробкиПередач": "Enum.ТипКоробкиПередач.Автомат",
                       "ТипТоплива": "Enum.ТипТоплива.Бензин", "ЦенаЗаСутки": "4500", "Статус": "Enum.СтатусыАвтомобиля.Свободен"}},
            {"id": "2", "name": "HyundaiSolaris", "code": "000000002", "description": "Hyundai Solaris В456КХ77",
             "attrs": {"Марка": "Hyundai", "Модель": "Solaris", "ГосНомер": "В456КХ77", "ГодВыпуска": "2021",
                       "Цвет": "Серый", "ТипКоробкиПередач": "Enum.ТипКоробкиПередач.Автомат",
                       "ТипТоплива": "Enum.ТипТоплива.Бензин", "ЦенаЗаСутки": "2800", "Статус": "Enum.СтатусыАвтомобиля.Свободен"}},
            {"id": "3", "name": "KiaRio", "code": "000000003", "description": "Kia Rio С789МН77",
             "attrs": {"Марка": "Kia", "Модель": "Rio", "ГосНомер": "С789МН77", "ГодВыпуска": "2020",
                       "Цвет": "Красный", "ТипКоробкиПередач": "Enum.ТипКоробкиПередач.Механика",
                       "ТипТоплива": "Enum.ТипТоплива.Бензин", "ЦенаЗаСутки": "2500", "Статус": "Enum.СтатусыАвтомобиля.Свободен"}},
            {"id": "4", "name": "BMWX5", "code": "000000004", "description": "BMW X5 Е111ОР77",
             "attrs": {"Марка": "BMW", "Модель": "X5", "ГосНомер": "Е111ОР77", "ГодВыпуска": "2023",
                       "Цвет": "Чёрный", "ТипКоробкиПередач": "Enum.ТипКоробкиПередач.Автомат",
                       "ТипТоплива": "Enum.ТипТоплива.Дизель", "ЦенаЗаСутки": "8500", "Статус": "Enum.СтатусыАвтомобиля.Свободен"}},
            {"id": "5", "name": "TeslaModel3", "code": "000000005", "description": "Tesla Model 3 К222ТТ77",
             "attrs": {"Марка": "Tesla", "Модель": "Model 3", "ГосНомер": "К222ТТ77", "ГодВыпуска": "2024",
                       "Цвет": "Синий", "ТипКоробкиПередач": "Enum.ТипКоробкиПередач.Автомат",
                       "ТипТоплива": "Enum.ТипТоплива.Электро", "ЦенаЗаСутки": "7000", "Статус": "Enum.СтатусыАвтомобиля.Свободен"}},
        ]))
        write(OUT / "Catalogs/Клиенты/Ext/Predefined.xml", predefined_catalog([
            {"id": "1", "name": "ИвановИван", "code": "000000001", "description": "Иванов Иван Петрович",
             "attrs": {"Телефон": "+7 (916) 123-45-67", "Адрес": "г. Москва, ул. Ленина, д. 10", "ДатаРождения": "1985-03-15", "НомерВУ": "77АА123456"}},
            {"id": "2", "name": "ПетроваАнна", "code": "000000002", "description": "Петрова Анна Сергеевна",
             "attrs": {"Телефон": "+7 (903) 987-65-43", "Адрес": "г. Москва, пр. Мира, д. 25", "ДатаРождения": "1990-07-22", "НомерВУ": "77ВВ654321"}},
            {"id": "3", "name": "СидоровАлексей", "code": "000000003", "description": "Сидоров Алексей Николаевич",
             "attrs": {"Телефон": "+7 (925) 555-12-34", "Адрес": "г. Химки, ул. Молодёжная, д. 5", "ДатаРождения": "1978-11-08", "НомерВУ": "50СС789012"}},
        ]))
        write(OUT / "Catalogs/Тарифы/Ext/Predefined.xml", predefined_catalog([
            {"id": "1", "name": "Эконом", "code": "000000001", "description": "Эконом",
             "attrs": {"БазоваяСкорость": "2000", "ЛимитКм": "200", "СтоимостьСверхлимита": "15"}},
            {"id": "2", "name": "Стандарт", "code": "000000002", "description": "Стандарт",
             "attrs": {"БазоваяСкорость": "3500", "ЛимитКм": "250", "СтоимостьСверхлимита": "20"}},
            {"id": "3", "name": "Бизнес", "code": "000000003", "description": "Бизнес",
             "attrs": {"БазоваяСкорость": "6000", "ЛимитКм": "300", "СтоимостьСверхлимита": "35"}},
            {"id": "4", "name": "Премиум", "code": "000000004", "description": "Премиум",
             "attrs": {"БазоваяСкорость": "10000", "ЛимитКм": "400", "СтоимостьСверхлимита": "50"}},
        ]))

    # --- Documents ---
    dog_attrs = [
        {"name": "Клиент", "synonym": "Клиент", "uuid": "f66d85b5-ccce-4183-9064-a5926a632226", "type": type_ref("CatalogRef.Клиенты"), "fill": "ShowError"},
        {"name": "Автомобиль", "synonym": "Автомобиль", "uuid": "cbededca-ca8a-4250-bca1-a2bb11550351", "type": type_ref("CatalogRef.Автомобили"), "fill": "ShowError"},
        {"name": "Тариф", "synonym": "Тариф", "uuid": "3a1a088c-8255-4433-9d22-c3ad6cf81ea9", "type": type_ref("CatalogRef.Тарифы"), "fill": "ShowError"},
        {"name": "ДатаНачала", "synonym": "Дата начала", "uuid": "b1df2e66-6c00-4996-a7ba-f69374ae5bc3", "type": type_date("Date"), "fill": "ShowError"},
        {"name": "ДатаОкончания", "synonym": "Дата окончания", "uuid": "869e2bb6-de2e-4632-8841-fbc2440c8593", "type": type_date("Date"), "fill": "ShowError"},
        {"name": "СуммаЗалога", "synonym": "Сумма залога", "uuid": "71754675-4db7-4ac0-95cb-50d4b88a4003", "type": type_number(15, 2, "Nonnegative")},
    ]
    write(OUT / "Documents/ДоговАренды.xml", document(
        "ДоговАренды", "Договор аренды", "3269621a-c4d0-4c05-8cc1-edc4294ddfa1", dog_attrs,
        register_records=["InformationRegister.СтатусыАвтомобилей", "InformationRegister.ЦеныПроката"],
    ))
    if not EDUCATIONAL_LITE:
        write(OUT / "Documents/ДоговАренды/Ext/ObjectModule.bsl", object_module_posting())

    fact_attrs = [
        {"name": "Договор", "synonym": "Договор", "uuid": "a0f00ce1-d8f6-45e8-99f6-4229152d756c", "type": type_ref("DocumentRef.ДоговАренды"), "fill": "ShowError"},
        {"name": "ДатаВозврата", "synonym": "Дата возврата", "uuid": "55a4585d-6b45-455b-b740-f37dfe0f2015", "type": type_date("DateTime"), "fill": "ShowError"},
        {"name": "КоличествоСуток", "synonym": "Количество суток", "uuid": "d847b952-1dc1-42d0-a564-fc76ae0a33c7", "type": type_number(5, 0, "Nonnegative")},
        {"name": "ЦенаЗаСутки", "synonym": "Цена за сутки", "uuid": "85dafba4-9de7-457b-b52b-7ab02c220f10", "type": type_number(15, 2, "Nonnegative")},
        {"name": "ПробегФакт", "synonym": "Пробег (км)", "uuid": "be7ff169-f4ea-4699-8657-3662d3ee3100", "type": type_number(10, 0, "Nonnegative")},
        {"name": "ДопРасходы", "synonym": "Доп. расходы", "uuid": "d4f27a27-5450-4f99-bc47-cb592907ec5b", "type": type_number(15, 2, "Nonnegative")},
        {"name": "ИтоговаяСумма", "synonym": "Итоговая сумма", "uuid": "7dc259d8-a107-42bf-ba24-f281e02f1421", "type": type_number(15, 2, "Nonnegative")},
    ]
    write(OUT / "Documents/ФактПроката.xml", document(
        "ФактПроката", "Факт проката", "7a5caa62-55b5-4ba0-8873-226855e5e260", fact_attrs,
        register_records=["AccumulationRegister.АрендаОбороты", "AccumulationRegister.ВзаиморасчетыСКлиентами",
                          "InformationRegister.СтатусыАвтомобилей"],
        forms=[] if EDUCATIONAL_LITE else ["ФормаДокумента"],
    ))
    if not EDUCATIONAL_LITE:
        write(OUT / "Documents/ФактПроката/Ext/ObjectModule.bsl", """Процедура ОбработкаПроведения(Отказ, РежимПроведения)

\tЕсли КоличествоСуток = 0 И ЗначениеЗаполнено(ДатаВозврата) Тогда
\t\tКоличествоСуток = Цел((ДатаВозврата - Договор.ДатаНачала) / 86400);
\tКонецЕсли;

\tЕсли ИтоговаяСумма = 0 Тогда
\t\tИтоговаяСумма = КоличествоСуток * ЦенаЗаСутки + ДопРасходы;
\tКонецЕсли;

КонецПроцедуры
""")
        form_uuid = "d117bdee-33be-4433-9115-210cf9dd4857"
        write(OUT / "Documents/ФактПроката/Forms/ФормаДокумента.xml", document_form_meta(form_uuid))
        write(OUT / "Documents/ФактПроката/Forms/ФормаДокумента/Ext/Form.xml",
              document_item_form("ФактПроката", ["Договор", "ДатаВозврата", "КоличествоСуток", "ЦенаЗаСутки", "ПробегФакт", "ДопРасходы", "ИтоговаяСумма"]))

    # --- Enums ---
    write(OUT / "Enums/ТипКоробкиПередач.xml", enum_obj("ТипКоробкиПередач", "Тип коробки передач", "cf385ce6-f503-4362-bb02-23472de2ad2d", [
        {"name": "Механика", "synonym": "Механика", "uuid": "9c6514c9-67bb-4b52-aa37-d59c3f16be7d"},
        {"name": "Автомат", "synonym": "Автомат", "uuid": "a6fa472d-60fd-4056-9f19-b8c1e0364612"},
        {"name": "Робот", "synonym": "Робот", "uuid": "011f9a03-b6a6-4a64-b52a-3273805b9fec"},
        {"name": "Вариатор", "synonym": "Вариатор", "uuid": "3f6591be-7953-4fd9-93b3-4a60be826112"},
    ]))
    write(OUT / "Enums/ТипТоплива.xml", enum_obj("ТипТоплива", "Тип топлива", "8aec2149-31a0-4acd-b83b-d2f339805ebf", [
        {"name": "Бензин", "synonym": "Бензин", "uuid": "2af420d1-dbd7-472f-bc8f-6921935c18fc"},
        {"name": "Дизель", "synonym": "Дизель", "uuid": "4b1d201b-6ed5-4336-b4a1-d474513be7e5"},
        {"name": "Гибрид", "synonym": "Гибрид", "uuid": "8d61bfc0-08a0-4d29-b34c-22cb38fdb7e9"},
        {"name": "Электро", "synonym": "Электро", "uuid": "7b1752a0-0b99-4e82-a319-1fbae9b95ce9"},
        {"name": "Метан", "synonym": "Метан", "uuid": "3edb4a0a-0fb1-4a3c-b0e8-ea747ccb35bb"},
    ]))
    write(OUT / "Enums/СтатусыАвтомобиля.xml", enum_obj("СтатусыАвтомобиля", "Статусы автомобиля", "5eda2f60-d968-4a55-9aa5-acf577d9e99c", [
        {"name": "Свободен", "synonym": "Свободен", "uuid": "a10a3753-ac6d-4a9a-b415-69d398ee1488"},
        {"name": "Занят", "synonym": "Занят", "uuid": "e1150620-db06-4424-9fee-5758b441e561"},
        {"name": "ВременноНедоступен", "synonym": "Временно недоступен", "uuid": "fdf9d95b-12f3-416b-abac-f582ecab0bce"},
    ]))

    # --- Information Registers ---
    def info_register(name, synonym_text, obj_uuid, dims, resources, periodicity="Day"):
        dims_xml = "\n".join(info_reg_dimension(d["name"], d["synonym"], d["type"], d["uuid"]) for d in dims)
        res_xml = "\n".join(info_reg_resource(r["name"], r["synonym"], r["type"], r["uuid"]) for r in resources)
        return (
            header()
            + f'\t<InformationRegister uuid="{obj_uuid}">\n'
            + "\t\t<InternalInfo>\n" + info_register_generated(name) + "\n\t\t</InternalInfo>\n"
            + "\t\t<Properties>\n"
            + f"\t\t\t<Name>{name}</Name>\n{synonym(synonym_text)}\n\t\t\t<Comment/>\n"
            + "\t\t\t<UseStandardCommands>true</UseStandardCommands>\n"
            + "\t\t\t<EditType>InDialog</EditType>\n"
            + "\t\t\t<DefaultRecordForm/>\n\t\t\t<DefaultListForm/>\n"
            + "\t\t\t<AuxiliaryRecordForm/>\n\t\t\t<AuxiliaryListForm/>\n"
            + "\t\t\t<StandardAttributes>\n" + register_std_attrs() + "\n\t\t\t</StandardAttributes>\n"
            + f"\t\t\t<InformationRegisterPeriodicity>{periodicity}</InformationRegisterPeriodicity>\n"
            + "\t\t\t<WriteMode>Independent</WriteMode>\n"
            + "\t\t\t<MainFilterOnPeriod>true</MainFilterOnPeriod>\n"
            + "\t\t\t<IncludeHelpInContents>false</IncludeHelpInContents>\n"
            + "\t\t\t<DataLockControlMode>Managed</DataLockControlMode>\n"
            + "\t\t\t<FullTextSearch>Use</FullTextSearch>\n"
            + "\t\t\t<EnableTotalsSliceFirst>false</EnableTotalsSliceFirst>\n"
            + "\t\t\t<EnableTotalsSliceLast>false</EnableTotalsSliceLast>\n"
            + "\t\t\t<RecordPresentation/>\n\t\t\t<ExtendedRecordPresentation/>\n"
            + "\t\t\t<ListPresentation/>\n\t\t\t<ExtendedListPresentation/>\n"
            + "\t\t\t<Explanation/>\n\t\t\t<DataHistory>DontUse</DataHistory>\n"
            + "\t\t\t<UpdateDataHistoryImmediatelyAfterWrite>false</UpdateDataHistoryImmediatelyAfterWrite>\n"
            + "\t\t\t<ExecuteAfterWriteDataHistoryVersionProcessing>false</ExecuteAfterWriteDataHistoryVersionProcessing>\n"
            + "\t\t</Properties>\n\t\t<ChildObjects>\n"
            + dims_xml + "\n" + res_xml
            + "\n\t\t</ChildObjects>\n\t</InformationRegister>\n" + footer()
        )

    write(OUT / "InformationRegisters/ЦеныПроката.xml", info_register(
        "ЦеныПроката", "Цены проката", "8f16f6df-2bfe-4a19-b935-c78c813866a3",
        [{"name": "Автомобиль", "synonym": "Автомобиль", "uuid": "c2891b2d-1287-4fba-8cde-d4f123ccbf76", "type": type_ref("CatalogRef.Автомобили")}],
        [{"name": "Цена", "synonym": "Цена за сутки", "uuid": "14a72a25-1ce3-467e-bbee-566d9ba1b309", "type": type_number(15, 2, "Nonnegative")}],
    ))
    write(OUT / "InformationRegisters/СтатусыАвтомобилей.xml", info_register(
        "СтатусыАвтомобилей", "Статусы автомобилей", "d87f1eac-3197-4ee6-a93a-6d4ab8ae2a99",
        [{"name": "Автомобиль", "synonym": "Автомобиль", "uuid": "bf463816-f6ac-47cc-8948-87bf719ad912", "type": type_ref("CatalogRef.Автомобили")}],
        [{"name": "Статус", "synonym": "Статус", "uuid": "3880109a-3375-4518-b54c-dafb57cc1900", "type": type_ref("EnumRef.СтатусыАвтомобиля")}],
        periodicity="Day",
    ))

    # --- Accumulation Registers ---
    def accum_register(name, synonym_text, obj_uuid, dims, resources, reg_type="Turnovers"):
        dims_xml = "\n".join(accum_reg_dimension(d["name"], d["synonym"], d["type"], d["uuid"]) for d in dims)
        res_xml = "\n".join(accum_reg_resource(r["name"], r["synonym"], r["type"], r["uuid"]) for r in resources)
        return (
            header()
            + f'\t<AccumulationRegister uuid="{obj_uuid}">\n'
            + "\t\t<InternalInfo>\n" + accum_register_generated(name) + "\n\t\t</InternalInfo>\n"
            + "\t\t<Properties>\n"
            + f"\t\t\t<Name>{name}</Name>\n{synonym(synonym_text)}\n\t\t\t<Comment/>\n"
            + "\t\t\t<UseStandardCommands>true</UseStandardCommands>\n"
            + "\t\t\t<DefaultListForm/>\n\t\t\t<AuxiliaryListForm/>\n"
            + f"\t\t\t<RegisterType>{reg_type}</RegisterType>\n"
            + "\t\t\t<IncludeHelpInContents>false</IncludeHelpInContents>\n"
            + "\t\t\t<StandardAttributes>\n" + register_std_attrs() + "\n\t\t\t</StandardAttributes>\n"
            + "\t\t\t<DataLockControlMode>Managed</DataLockControlMode>\n"
            + "\t\t\t<FullTextSearch>Use</FullTextSearch>\n"
            + "\t\t\t<EnableTotalsSplitting>true</EnableTotalsSplitting>\n"
            + "\t\t\t<ListPresentation/>\n\t\t\t<ExtendedListPresentation/>\n"
            + "\t\t\t<Explanation/>\n\t\t</Properties>\n\t\t<ChildObjects>\n"
            + dims_xml + "\n" + res_xml
            + "\n\t\t</ChildObjects>\n\t</AccumulationRegister>\n" + footer()
        )

    write(OUT / "AccumulationRegisters/АрендаОбороты.xml", accum_register(
        "АрендаОбороты", "Аренда (обороты)", "dbb35aee-8f04-49fd-8954-23e82d28f63f",
        [
            {"name": "Клиент", "synonym": "Клиент", "uuid": "b18a581f-7f7b-4429-990a-d7678419bc05", "type": type_ref("CatalogRef.Клиенты")},
            {"name": "Автомобиль", "synonym": "Автомобиль", "uuid": "7ec7d4dc-3fee-4783-85d4-f4d9b1ee8a2f", "type": type_ref("CatalogRef.Автомобили")},
            {"name": "Договор", "synonym": "Договор", "uuid": "3069b9ab-19cf-46b6-9804-8a735818609c", "type": type_ref("DocumentRef.ДоговАренды")},
        ],
        [
            {"name": "КоличествоДней", "synonym": "Количество дней", "uuid": "df03bab9-32f6-4432-9383-faca9001668f", "type": type_number(10, 0, "Nonnegative")},
            {"name": "Сумма", "synonym": "Сумма", "uuid": "34894c88-e9c7-435f-98e7-6c29ca5b6bcf", "type": type_number(15, 2, "Any")},
        ],
    ))
    write(OUT / "AccumulationRegisters/ВзаиморасчетыСКлиентами.xml", accum_register(
        "ВзаиморасчетыСКлиентами", "Взаиморасчёты с клиентами", "f45c583e-fed8-42a8-9e57-afbf535bc881",
        [{"name": "Клиент", "synonym": "Клиент", "uuid": "4557a958-e4ff-4376-aee9-0b8b9b50d0b1", "type": type_ref("CatalogRef.Клиенты")}],
        [{"name": "Сумма", "synonym": "Сумма", "uuid": "d15c35c4-a3f4-406a-a8fc-77a51b00b8fe", "type": type_number(15, 2, "Any")}],
        reg_type="Balance",
    ))

    # --- Reports (minimal) ---
    def report(name, synonym_text, obj_uuid, template_uuid):
        return (
            header()
            + f'\t<Report uuid="{obj_uuid}">\n'
            + "\t\t<InternalInfo>\n" + report_generated(name) + "\n\t\t</InternalInfo>\n"
            + "\t\t<Properties>\n"
            + f"\t\t\t<Name>{name}</Name>\n{synonym(synonym_text)}\n\t\t\t<Comment/>\n"
            + "\t\t\t<UseStandardCommands>true</UseStandardCommands>\n"
            + "\t\t\t<DefaultForm/>\n\t\t\t<AuxiliaryForm/>\n"
            + f"\t\t\t<MainDataCompositionSchema>Report.{name}.Template.ОсновнаяСхемаКомпоновкиДанных</MainDataCompositionSchema>\n"
            + "\t\t\t<DefaultSettingsForm/>\n\t\t\t<AuxiliarySettingsForm/>\n"
            + "\t\t\t<DefaultVariantForm/>\n\t\t\t<VariantsStorage/>\n\t\t\t<SettingsStorage/>\n"
            + "\t\t\t<IncludeHelpInContents>false</IncludeHelpInContents>\n"
            + "\t\t\t<ExtendedPresentation/>\n\t\t\t<Explanation/>\n"
            + "\t\t</Properties>\n\t\t<ChildObjects>\n"
            + "\t\t\t<Template>ОсновнаяСхемаКомпоновкиДанных</Template>\n"
            + "\t\t</ChildObjects>\n\t</Report>\n" + footer()
        )

    reports = [
        ("ДоходыОтПроката", "Доходы от проката", "562f400a-2d95-4be6-b931-71f0c000fd38", "d62e88a6-b77f-4767-b171-ee25bbbbdfb8"),
        ("СостояниеАвтопарка", "Состояние автопарка", "7f4219ef-ab63-4fd9-937b-c258a526d247", "ba3ede61-0ebb-4fec-b482-f1070c08dca7"),
        ("ИсторияАвтомобилей", "История автомобилей", "a91bb7fd-30e3-4255-9561-c0417ac61662", "f219e6ff-d12b-48e7-a793-9db8e3043aa5"),
    ]
    dcs_template = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<DataCompositionSchema xmlns="http://v8.1c.ru/8.1/data-composition-system/schema" '
        'xmlns:dcscom="http://v8.1c.ru/8.1/data-composition-system/common" '
        'xmlns:dcscor="http://v8.1c.ru/8.1/data-composition-system/core" '
        'xmlns:dcsset="http://v8.1c.ru/8.1/data-composition-system/settings" '
        'xmlns:v8="http://v8.1c.ru/8.1/data/core" '
        'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">\n'
        '\t<dataSource>\n\t\t<name>ИсточникДанных1</name>\n'
        '\t\t<dataSourceType>Local</dataSourceType>\n\t</dataSource>\n'
        '\t<dataSet xsi:type="DataSetQuery">\n\t\t<name>НаборДанных1</name>\n'
        '\t\t<field xsi:type="DataSetFieldField">\n\t\t\t<dataPath>Поле1</dataPath>\n'
        '\t\t\t<field>Поле1</field>\n\t\t\t<title xsi:type="v8:LocalStringType">\n'
        '\t\t\t\t<v8:item><v8:lang>ru</v8:lang><v8:content>Поле</v8:content></v8:item>\n'
        '\t\t\t</title>\n\t\t</field>\n\t\t<dataSource>ИсточникДанных1</dataSource>\n'
        '\t\t<query>ВЫБРАТЬ 1 КАК Поле1</query>\n\t</dataSet>\n'
        '\t<settingsVariant>\n\t\t<dcsset:name>Основной</dcsset:name>\n'
        '\t\t<dcsset:presentation xsi:type="v8:LocalStringType">\n'
        '\t\t\t<v8:item><v8:lang>ru</v8:lang><v8:content>Основной</v8:content></v8:item>\n'
        '\t\t</dcsset:presentation>\n\t\t<dcsset:settings xmlns:style="http://v8.1c.ru/8.1/data/ui/style" '
        'xmlns:sys="http://v8.1c.ru/8.1/data/ui/fonts/system" '
        'xmlns:web="http://v8.1c.ru/8.1/data/ui/colors/web" '
        'xmlns:win="http://v8.1c.ru/8.1/data/ui/colors/windows"/>\n'
        '\t</settingsVariant>\n</DataCompositionSchema>\n'
    )
    if not EDUCATIONAL_LITE:
        for rname, rsyn, ruuid, tuuid in reports:
            write(OUT / f"Reports/{rname}.xml", report(rname, rsyn, ruuid, tuuid))
            write(OUT / f"Reports/{rname}/Templates/ОсновнаяСхемаКомпоновкиДанных.xml",
                  header() + f'\t<Template uuid="{tuuid}">\n\t\t<Properties>\n\t\t\t<Name>ОсновнаяСхемаКомпоновкиДанных</Name>\n'
                  + synonym("Основная схема компоновки данных", "\t\t\t")
                  + '\n\t\t\t<Comment/>\n\t\t\t<TemplateType>DataCompositionSchema</TemplateType>\n'
                  + '\t\t</Properties>\n\t</Template>\n' + footer())
            write(OUT / f"Reports/{rname}/Templates/ОсновнаяСхемаКомпоновкиДанных/Ext/Template.xml", dcs_template)

    # --- Subsystems ---
    write(OUT / "Subsystems/Справочники.xml", subsystem(
        "Справочники", "Справочники", "37e0dd5e-aa1a-41b9-aff9-863b08d953b7",
        ["Catalog.Автомобили", "Catalog.Клиенты", "Catalog.Тарифы"],
    ))
    write(OUT / "Subsystems/УчетАвтомобилей.xml", subsystem(
        "УчетАвтомобилей", "Учёт автомобилей", "54ac6afe-aa6b-4d8f-9be6-1472746b92b7",
        ["Catalog.Автомобили", "InformationRegister.СтатусыАвтомобилей"]
        + ([] if EDUCATIONAL_LITE else ["Report.СостояниеАвтопарка", "Report.ИсторияАвтомобилей"]),
    ))
    write(OUT / "Subsystems/УчётКлиентов.xml", subsystem(
        "УчётКлиентов", "Учёт клиентов", "5352d185-a2c9-4d50-8416-98e155d8c959",
        ["Catalog.Клиенты", "AccumulationRegister.ВзаиморасчетыСКлиентами"],
    ))
    write(OUT / "Subsystems/Прокат.xml", subsystem(
        "Прокат", "Прокат", "47ba7ca8-63ea-4330-9bfd-dc5370d3bd87",
        ["Document.ДоговАренды", "Document.ФактПроката", "Catalog.Тарифы",
         "InformationRegister.ЦеныПроката", "AccumulationRegister.АрендаОбороты"]
        + ([] if EDUCATIONAL_LITE else ["Report.ДоходыОтПроката"]),
    ))

    # --- Roles ---
    write(OUT / "Roles/Администратор.xml", role("Администратор", "Администратор", "a73a2861-49f2-4e49-abef-0548278b200c"))
    write(OUT / "Roles/Администратор/Ext/Rights.xml", simple_rights() if EDUCATIONAL_LITE else rights_all_objects())
    if not EDUCATIONAL_LITE:
        write(OUT / "Roles/ВсеПрава.xml", role("ВсеПрава", "Полные права", "56763445-c5b2-4661-98e3-708ffcb8b584"))
        write(OUT / "Roles/ВсеПрава/Ext/Rights.xml", rights_all_objects())
        write(OUT / "Roles/Менеджер.xml", role("Менеджер", "Менеджер", "03daec1e-f6ad-43eb-a08b-c61c99558ad0"))
        mgr_objs = [
            "Catalog.Автомобили", "Catalog.Клиенты", "Catalog.Тарифы",
            "Document.ДоговАренды", "Document.ФактПроката",
            "InformationRegister.ЦеныПроката", "InformationRegister.СтатусыАвтомобилей",
            "AccumulationRegister.АрендаОбороты", "AccumulationRegister.ВзаиморасчетыСКлиентами",
            "Report.ДоходыОтПроката", "Report.СостояниеАвтопарка", "Report.ИсторияАвтомобилей",
        ]
        write(OUT / "Roles/Менеджер/Ext/Rights.xml", manager_rights(mgr_objs))

    # --- Language ---
    write(OUT / "Languages/Русский.xml", (
        header()
        + '\t<Language uuid="ece63e2c-d3df-4b8a-87b5-80c9d04ab3ab">\n'
        + "\t\t<Properties>\n\t\t\t<Name>Русский</Name>\n"
        + synonym("Русский")
        + "\n\t\t\t<Comment/>\n\t\t\t<LanguageCode>ru</LanguageCode>\n"
        + "\t\t</Properties>\n\t</Language>\n" + footer()
    ))

    # --- Configuration.xml ---
    src_cfg = Path("/home/ubuntu/.cursor/projects/workspace/uploads/Configuration_6471.xml")
    cfg_text = src_cfg.read_text(encoding="utf-8")
    cfg_text = cfg_text.replace("<Synonym/>", (
        "<Synonym>\n\t\t\t\t<v8:item>\n\t\t\t\t\t<v8:lang>ru</v8:lang>\n"
        "\t\t\t\t\t<v8:content>Автопрокат — учёт аренды автомобилей</v8:content>\n"
        "\t\t\t\t</v8:item>\n\t\t\t</Synonym>"
    ), 1)
    cfg_text = cfg_text.replace("<BriefInformation/>", (
        "<BriefInformation>\n\t\t\t\t<v8:item>\n\t\t\t\t\t<v8:lang>ru</v8:lang>\n"
        "\t\t\t\t\t<v8:content>Конфигурация для учёта проката автомобилей</v8:content>\n"
        "\t\t\t\t</v8:item>\n\t\t\t</BriefInformation>"
    ))
    cfg_text = cfg_text.replace("<DefaultRoles/>", (
        "<DefaultRoles>\n\t\t\t\t<xr:Item xsi:type=\"xr:MDObjectRef\">Role.Администратор</xr:Item>\n"
        + ("" if EDUCATIONAL_LITE else "\t\t\t\t<xr:Item xsi:type=\"xr:MDObjectRef\">Role.ВсеПрава</xr:Item>\n")
        + "\t\t\t</DefaultRoles>"
    ))
    cfg_text = cfg_text.replace("<Vendor/>", "<Vendor>Автопрокат</Vendor>")
    cfg_text = cfg_text.replace("<Version/>", "<Version>1.0.0.1</Version>")
    write(OUT / "Configuration.xml", downgrade_configuration(cfg_text))

    # --- ConfigDumpInfo.xml ---
    src_dump = Path("/home/ubuntu/.cursor/projects/workspace/uploads/ConfigDumpInfo_afcd.xml")
    dump_text = src_dump.read_text(encoding="utf-8")
    dump_text = re.sub(r'version="2\.\d+"', f'version="{VERSION}"', dump_text, count=1)
    dump_text = dump_text.replace(
        '\t\t<Metadata name="Configuration.Конфигурация.StandaloneConfigurationContent" '
        'id="b8ba0334-844c-44ad-8069-50de0a73125a.f" configVersion="2b2ed05e8d8b8348be88a8f0d7ea4a5900000000"/>\n',
        "",
    )
    dump_text = filter_config_dump_info(dump_text)
    if EDUCATIONAL_LITE:
        dump_text = re.sub(
            r'\t\t<Metadata name="Document\.ДоговАренды\.ObjectModule".*?\n',
            "",
            dump_text,
        )
        dump_text = re.sub(
            r'\t\t<Metadata name="Document\.ФактПроката\.ObjectModule".*?\n',
            "",
            dump_text,
        )
    write(OUT / "ConfigDumpInfo.xml", dump_text)

    write(OUT / "!!! ЗАГРУЖАТЬ ИЗ ЭТОЙ ПАПКИ !!!.txt", (
        "ВАЖНО: при загрузке в 1С выберите именно ЭТУ папку (1c-config),\n"
        "а не корень репозитория RepositoryGit!\n\n"
        "В этой папке должны лежать файлы:\n"
        "  - Configuration.xml\n"
        "  - ConfigDumpInfo.xml\n"
        "  - папки Catalogs, Documents, Enums и др.\n\n"
        "Формат выгрузки: 2.10 (учебная платформа 8.3.17).\n"
        "Облегчённая сборка: без отчётов и предзаполненных данных.\n"
        "Данные в справочники можно внести вручную после загрузки.\n\n"
        "Конфигуратор → Конфигурация → Загрузить конфигурацию из файлов...\n"
        "Укажите путь к папке 1c-config\n"
    ))

    print(f"Generated config in {OUT}")
    print(f"Total files: {sum(1 for _ in OUT.rglob('*') if _.is_file())}")


if __name__ == "__main__":
    main()
