"""数据库初始化与种子数据（首次启动时写入示例数据，便于直接体验）。"""

from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.crypto import encrypt_field
from app.core.database import SessionLocal
from app.core.security import hash_password
from app.modules.assets.models import KIND_MAJOR, KIND_SUB, MAJOR_CATEGORIES, Asset, Category, Tag
from app.modules.auth.models import User
from app.modules.org.models import TYPE_BUILDING, TYPE_CLASS, TYPE_PARK, OrgUnit

DEFAULT_PASSWORD = "admin123"


def init_db() -> None:
    """幂等初始化：若已存在 admin 账号则跳过。"""
    db = SessionLocal()
    try:
        if db.scalar(select(User).where(User.username == "admin")):
            return
        _seed(db)
    finally:
        db.close()


def _seed(db: Session) -> None:
    # ---------- 组织域（园区 → 楼栋 → 班级） ----------
    park = OrgUnit(name="阳光幼儿园", parent_id=None, type=TYPE_PARK)
    db.add(park)
    db.flush()
    building1 = OrgUnit(name="1号楼", parent_id=park.id, type=TYPE_BUILDING)
    building2 = OrgUnit(name="2号楼", parent_id=park.id, type=TYPE_BUILDING)
    db.add_all([building1, building2])
    db.flush()
    classrooms = {
        "小一班": OrgUnit(name="小一班", parent_id=building1.id, type=TYPE_CLASS),
        "中一班": OrgUnit(name="中一班", parent_id=building1.id, type=TYPE_CLASS),
        "大一班": OrgUnit(name="大一班", parent_id=building2.id, type=TYPE_CLASS),
    }
    db.add_all(classrooms.values())
    db.flush()

    # ---------- 用户（含数据域与数据范围） ----------
    users = [
        User(username="admin", password_hash=hash_password(DEFAULT_PASSWORD), full_name="园长",
             role="admin", phone=encrypt_field("13800001234"), org_unit_id=park.id, data_scope="all"),
        User(username="logistics", password_hash=hash_password(DEFAULT_PASSWORD), full_name="王后勤",
             role="logistics", phone=encrypt_field("13900005678"), org_unit_id=building1.id, data_scope="org"),
        User(username="teacher", password_hash=hash_password(DEFAULT_PASSWORD), full_name="左老师",
             role="teacher", phone=encrypt_field("13700009012"), org_unit_id=classrooms["中一班"].id, data_scope="self"),
        User(username="caregiver", password_hash=hash_password(DEFAULT_PASSWORD), full_name="赵保育",
             role="caregiver", phone=encrypt_field("13600003456"), org_unit_id=classrooms["中一班"].id, data_scope="self"),
    ]
    db.add_all(users)
    db.flush()

    # ---------- 分类（资产大类 → 子类） ----------
    majors: dict[str, Category] = {
        name: Category(name=name, parent_id=None, kind=KIND_MAJOR, description="")
        for name in MAJOR_CATEGORIES
    }
    db.add_all(majors.values())
    db.flush()

    sub_defs = {
        "玩具": ["益智玩具", "建构玩具"],
        "教具": ["数学教具", "语言教具"],
        "图书绘本": ["绘本", "科普读物"],
        "教学设备": ["多媒体设备", "乐器"],
        "电器家具": ["空调", "冰箱", "洗衣机", "饮水机", "消毒柜", "幼教桌椅", "办公家具"],
        "体育器材": ["球类", "攀爬器械"],
        "办公用品": ["打印耗材", "办公文具", "办公设备"],
        "生活用品": ["被褥", "园服", "餐具", "厨具", "幼儿床铺"],
        "消防安防": ["灭火器", "监控设备"],
        "其他": ["其他资产"],
    }
    subs: dict[str, Category] = {}
    for major_name, names in sub_defs.items():
        for name in names:
            subs[name] = Category(name=name, parent_id=majors[major_name].id, kind=KIND_SUB, description="")
    db.add_all(subs.values())
    db.flush()

    # ---------- 标签（五大领域） ----------
    tag_defs = [
        ("绘本阅读", "语言"),
        ("故事表演", "语言"),
        ("数学认知", "科学"),
        ("科学探究", "科学"),
        ("绘画", "艺术"),
        ("音乐律动", "艺术"),
        ("大肌肉", "健康"),
        ("精细动作", "健康"),
        ("角色扮演", "社会"),
    ]
    tags = {name: Tag(name=name, domain=domain) for name, domain in tag_defs}
    db.add_all(tags.values())
    db.flush()

    # ---------- 示例资产（覆盖多类资产；玩具仅为其中一类） ----------
    today = date.today()
    mid = classrooms["中一班"].id
    small = classrooms["小一班"].id
    big = classrooms["大一班"].id
    assets = [
        Asset(name="大颗粒积木套装", code="ZC00001", category_id=subs["建构玩具"].id, org_unit_id=mid,
              quantity=5, unit="套", location="中一班", age_range="4-5", safety_level="A",
              purchase_date=today - timedelta(days=200),
              disinfect_due=today + timedelta(days=3), safety_check_due=today + timedelta(days=20),
              tags=[tags["数学认知"], tags["精细动作"]]),
        Asset(name="儿童拼图板", code="ZC00002", category_id=subs["益智玩具"].id, org_unit_id=mid,
              quantity=8, unit="盒", location="资源室", age_range="3-4", safety_level="A",
              disinfect_due=today + timedelta(days=5), tags=[tags["数学认知"]]),
        Asset(name="绘本《好饿的毛毛虫》", code="ZC00003", category_id=subs["绘本"].id, org_unit_id=small,
              quantity=10, unit="本", location="阅读区", age_range="3-5", safety_level="A",
              tags=[tags["绘本阅读"]]),
        Asset(name="幼儿跳绳", code="ZC00004", category_id=subs["球类"].id, org_unit_id=big,
              quantity=20, unit="根", location="操场器材柜", age_range="5-6", safety_level="B",
              safety_check_due=today + timedelta(days=6), tags=[tags["大肌肉"]]),
        Asset(name="非洲鼓", code="ZC00005", category_id=subs["语言教具"].id, org_unit_id=mid,
              quantity=6, unit="个", location="音乐教室", age_range="4-6", safety_level="A",
              tags=[tags["音乐律动"]]),
        Asset(name="儿童安全剪刀", code="ZC00006", category_id=subs["其他资产"].id, org_unit_id=mid,
              quantity=15, unit="把", location="美工区", age_range="4-6", safety_level="B",
              safety_check_due=today - timedelta(days=1),  # 已逾期，用于演示预警
              tags=[tags["精细动作"], tags["绘画"]]),
        Asset(name="教学一体机", code="ZC00007", category_id=subs["多媒体设备"].id, org_unit_id=mid,
              quantity=1, unit="台", location="中一班教室", safety_level="A",
              safety_check_due=today + timedelta(days=30)),
        Asset(name="手提式干粉灭火器", code="ZC00008", category_id=subs["灭火器"].id, org_unit_id=building1.id,
              quantity=4, unit="具", location="1号楼走廊", safety_level="A",
              safety_check_due=today + timedelta(days=4)),
        Asset(name="幼儿午睡被褥", code="ZC00009", category_id=subs["被褥"].id, org_unit_id=mid,
              quantity=30, unit="套", location="中一班午睡室", safety_level="B",
              disinfect_due=today + timedelta(days=2)),
        Asset(name="幼儿篮球", code="ZC00010", category_id=subs["球类"].id, org_unit_id=big,
              quantity=12, unit="个", location="操场器材柜", age_range="4-6", safety_level="B",
              disinfect_due=today + timedelta(days=6), tags=[tags["大肌肉"]]),
        # ---- 以下为固定资产（座椅 / 餐具 / 空调 等，非玩具类） ----
        Asset(name="立式空调（3匹）", code="ZC00011", category_id=subs["空调"].id, org_unit_id=mid,
              quantity=2, unit="台", location="中一班教室", safety_level="A",
              purchase_date=today - timedelta(days=400),
              safety_check_due=today + timedelta(days=30)),
        Asset(name="幼儿靠背座椅", code="ZC00012", category_id=subs["幼教桌椅"].id, org_unit_id=mid,
              quantity=30, unit="把", location="中一班教室", age_range="3-6", safety_level="A",
              purchase_date=today - timedelta(days=300),
              safety_check_due=today + timedelta(days=25)),
        Asset(name="幼儿长方形餐桌", code="ZC00013", category_id=subs["幼教桌椅"].id, org_unit_id=mid,
              quantity=5, unit="张", location="中一班教室", age_range="3-6", safety_level="A",
              purchase_date=today - timedelta(days=300)),
        Asset(name="不锈钢分格餐盘", code="ZC00014", category_id=subs["餐具"].id, org_unit_id=mid,
              quantity=60, unit="个", location="厨房", safety_level="A",
              disinfect_due=today + timedelta(days=2)),
        Asset(name="不锈钢幼儿水杯", code="ZC00015", category_id=subs["餐具"].id, org_unit_id=mid,
              quantity=60, unit="个", location="中一班教室", safety_level="A",
              disinfect_due=today + timedelta(days=4)),
        Asset(name="高温消毒柜", code="ZC00016", category_id=subs["消毒柜"].id, org_unit_id=mid,
              quantity=1, unit="台", location="厨房", safety_level="A",
              purchase_date=today - timedelta(days=250),
              safety_check_due=today + timedelta(days=12)),
        Asset(name="幼儿午睡床", code="ZC00017", category_id=subs["幼儿床铺"].id, org_unit_id=mid,
              quantity=30, unit="张", location="中一班午睡室", safety_level="A",
              disinfect_due=today + timedelta(days=3)),
        Asset(name="教师办公电脑", code="ZC00018", category_id=subs["办公设备"].id, org_unit_id=building1.id,
              quantity=3, unit="台", location="教师办公室", safety_level="A"),
        Asset(name="保温饮水机", code="ZC00019", category_id=subs["饮水机"].id, org_unit_id=building1.id,
              quantity=2, unit="台", location="1号楼走廊", safety_level="A",
              safety_check_due=today + timedelta(days=18)),
        Asset(name="立式钢琴", code="ZC00020", category_id=subs["乐器"].id, org_unit_id=mid,
              quantity=1, unit="台", location="音乐教室", safety_level="A",
              purchase_date=today - timedelta(days=800)),
    ]
    db.add_all(assets)
    db.commit()
