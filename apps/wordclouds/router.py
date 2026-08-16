"""
Wordclouds API Router
Endpoints for Bible and Shakespeare wordcloud visualizations.
"""
import json
import pandas as pd
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(tags=["Wordclouds"])
templates = Jinja2Templates(directory="templates")


# Bible Wordclouds
@router.get("/bible/{testament}/{chapter}", tags=["Get wordclouds for chapter"])
async def get_bible_chapter(testament: str, chapter: str):
    chapter = str(chapter).zfill(2)
    img = f"./static/biblewordclouds/{testament}_{chapter}.png"
    return FileResponse(img)


@router.get("/bible/{testament}", tags=["Get wordclouds for testament"])
async def get_bible_testament(testament: str):
    df = pd.read_csv('./db/wordcloud.csv')
    df = df[df['testament'] == testament.lower()]
    df['link'] = df['book'].apply(lambda x: f"https://fleminganalytic.com/wordclouds/bible/{testament}/{x}")
    df.sort_values(by='book', ascending=True, inplace=True)
    parsed = df.to_json(orient='records')
    return json.loads(parsed)


@router.get("/bible/test")
async def get_bible_test():
    return FileResponse('./static/biblewordclouds/old_28.png')


@router.get("/bible/", response_class=HTMLResponse)
async def bible_page(request: Request):
    return templates.TemplateResponse("biblewordclouds.html", {"request": request})


# Shakespeare Wordclouds
@router.get("/shakespeare/{play}", tags=["Get Shakespeare Wordcloud for play"])
async def get_shakespeare_play(play: str):
    img = f"./static/shakespeare/{play}.png"
    return FileResponse(img)


@router.get("/shakespeare", tags=["Get Shakespeare Wordclouds"])
async def get_shakespeare_list():
    df = pd.read_csv('./db/shakespeare.csv')
    parsed = df.to_json(orient='records')
    return json.loads(parsed)


@router.get("/shakespeare/", response_class=HTMLResponse)
async def shakespeare_page(request: Request):
    return templates.TemplateResponse("shakespearewordclouds.html", {"request": request})
