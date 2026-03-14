from __future__ import annotations

import shutil
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.error import URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from backend.core.config import settings
from backend.db.session import SessionLocal, init_data_dirs, init_db
from backend.models import Category, Message, Product, ProductImage, ShopSetting

USER_AGENT = "Mozilla/5.0 (compatible; YRFasionDemoSeeder/1.0)"
IMAGE_WIDTH = 1400
DOWNLOAD_RETRIES = 3
DOWNLOAD_TIMEOUT_SECONDS = 90


@dataclass(frozen=True)
class DemoImageSource:
    filename: str
    page_url: str

    @property
    def download_url(self) -> str:
        encoded = quote(self.filename, safe="")
        return f"https://commons.wikimedia.org/wiki/Special:FilePath/{encoded}?width={IMAGE_WIDTH}"


@dataclass(frozen=True)
class DemoProductSeed:
    name: str
    category: str
    description: str
    tags: tuple[str, ...]
    status: str
    sort_order: int
    image: DemoImageSource


DEMO_CATEGORIES = (
    ("连衣裙", 1),
    ("半裙", 2),
    ("上装", 3),
    ("外套", 4),
)

DEMO_PRODUCTS = (
    DemoProductSeed(
        name="轻盈褶裥半裙",
        category="半裙",
        description="适合春夏通勤与日常出行的轻盈半裙，线条简洁，搭配空间充足。",
        tags=("精选", "春季"),
        status="published",
        sort_order=10,
        image=DemoImageSource(
            filename="Fashionable woman in a skirt (Unsplash).jpg",
            page_url="https://commons.wikimedia.org/wiki/File:Fashionable_woman_in_a_skirt_(Unsplash).jpg",
        ),
    ),
    DemoProductSeed(
        name="海岸感飘逸连衣裙",
        category="连衣裙",
        description="适合假日穿搭的飘逸轮廓，视觉上轻松自然，适合首页主推陈列。",
        tags=("度假", "轻盈"),
        status="published",
        sort_order=20,
        image=DemoImageSource(
            filename="Corfu, Greece (Unsplash OMGeAs 4goY).jpg",
            page_url="https://commons.wikimedia.org/wiki/File:Corfu,_Greece_(Unsplash_OMGeAs_4goY).jpg",
        ),
    ),
    DemoProductSeed(
        name="城市感短外套",
        category="外套",
        description="具有街头层次感的短外套单品，适合作为管理后台商品封面演示。",
        tags=("通勤", "秋装"),
        status="published",
        sort_order=30,
        image=DemoImageSource(
            filename="Fashionable Faux Fur (Unsplash).jpg",
            page_url="https://commons.wikimedia.org/wiki/File:Fashionable_Faux_Fur_(Unsplash).jpg",
        ),
    ),
    DemoProductSeed(
        name="露肩设计上衣",
        category="上装",
        description="用于展示轻时装风格的上衣单品，适合首页精选与商品详情页演示。",
        tags=("精选", "约会"),
        status="published",
        sort_order=40,
        image=DemoImageSource(
            filename="Off The Shoulder Blouse (Unsplash).jpg",
            page_url="https://commons.wikimedia.org/wiki/File:Off_The_Shoulder_Blouse_(Unsplash).jpg",
        ),
    ),
)


def download_image(source: DemoImageSource) -> tuple[bytes, str]:
    content = b""
    content_type = ""
    last_error: Exception | None = None

    for attempt in range(1, DOWNLOAD_RETRIES + 1):
        request = Request(source.download_url, headers={"User-Agent": USER_AGENT})
        try:
            with urlopen(request, timeout=DOWNLOAD_TIMEOUT_SECONDS) as response:
                content_type = response.headers.get("Content-Type", "")
                content = response.read()
            break
        except URLError as exc:
            last_error = exc
            if attempt == DOWNLOAD_RETRIES:
                raise
            time.sleep(attempt)

    if last_error is not None and not content:
        raise last_error

    if not content_type.startswith("image/"):
        raise RuntimeError(f"Unexpected response for {source.filename}: {content_type}")

    suffix = Path(source.filename).suffix.lower() or ".jpg"
    if suffix not in {".jpg", ".jpeg", ".png", ".webp"}:
        suffix = ".jpg"
    return content, suffix


def download_assets() -> dict[str, tuple[bytes, str]]:
    assets: dict[str, tuple[bytes, str]] = {}
    for seed in DEMO_PRODUCTS:
        assets[seed.name] = download_image(seed.image)
    return assets


def reset_product_uploads() -> None:
    products_dir = settings.resolved_upload_dir / "products"
    if products_dir.exists():
        shutil.rmtree(products_dir)
    products_dir.mkdir(parents=True, exist_ok=True)


def seed_demo_catalog(assets: dict[str, tuple[bytes, str]]) -> None:
    init_data_dirs()
    init_db()
    reset_product_uploads()

    with SessionLocal() as db:
        db.query(Message).delete()
        db.query(ProductImage).delete()
        db.query(Product).delete()
        db.query(Category).delete()
        db.commit()

        category_map: dict[str, Category] = {}
        for name, sort_order in DEMO_CATEGORIES:
            category = Category(name=name, status="active", sort_order=sort_order)
            db.add(category)
            db.flush()
            category_map[name] = category

        banner_urls: list[str] = []
        for index, seed in enumerate(DEMO_PRODUCTS):
            product = Product(
                name=seed.name,
                category_id=category_map[seed.category].id,
                description=seed.description,
                tags_json=list(seed.tags),
                status=seed.status,
                sort_order=seed.sort_order,
            )
            db.add(product)
            db.flush()

            content, suffix = assets[seed.name]
            relative_dir = Path("products") / str(product.id)
            target_dir = settings.resolved_upload_dir / relative_dir
            target_dir.mkdir(parents=True, exist_ok=True)

            filename = f"cover{suffix}"
            relative_path = relative_dir / filename
            absolute_path = settings.resolved_upload_dir / relative_path
            absolute_path.write_bytes(content)

            image_url = f"/uploads/{relative_path.as_posix()}"
            db.add(
                ProductImage(
                    product_id=product.id,
                    storage_type="local",
                    storage_path=relative_path.as_posix(),
                    image_url=image_url,
                    original_name=seed.image.filename,
                    sort_order=0,
                    is_cover=True,
                )
            )

            if index < 2:
                banner_urls.append(image_url)

        shop_setting = db.get(ShopSetting, 1)
        if shop_setting is None:
            shop_setting = ShopSetting(id=1)
            db.add(shop_setting)

        shop_setting.shop_name = "YRFasion 时装馆"
        shop_setting.shop_intro = "精选女装与轻时尚穿搭，支持管理后台与小程序联调演示。"
        shop_setting.contact_phone = "13815251939"
        shop_setting.wechat_id = "yrfasion-shop"
        shop_setting.address = "南京市鼓楼区汉中路 176 号"
        shop_setting.business_hours = "10:00-21:00"
        shop_setting.homepage_banner_json = banner_urls

        db.commit()


def print_summary() -> None:
    print("Demo catalog refreshed:")
    for seed in DEMO_PRODUCTS:
        print(f"- {seed.name} | {seed.category} | {seed.image.page_url}")


def main() -> None:
    assets = download_assets()
    seed_demo_catalog(assets)
    print_summary()


if __name__ == "__main__":
    main()
