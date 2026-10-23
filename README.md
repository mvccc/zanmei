## Tools for Service

### 按模板製作ppt

```bash
$ make init # do it once
$ cat services/2019-03-24.flags
--choir=236_大哉聖哉耶穌尊名2

--hymns=坐在寶座上聖潔羔羊
--hymns=114_主曾離寳座
--hymns=最知心的朋友
--hymns=343_更像我恩主
--response=298_為主而活
--offering=488-1_獻上感恩的心

--call_scripture=詩篇95:6-7
--scripture=馬太福音25:14-30
--memorize=馬太福音25:23

--message=今日教會所需要的人才
--messager=姜武城牧師

$ make slides SUNDAY=2019-03-24
$ open 2019-03-24.pptx
```

### Reusable Song Arrangements

Keep complete lyrics in `processed/mvccc/*.md`. Each `##` section is one lyric
slide; edit its line breaks there, preferably keeping 3-5 lines per page.
The generator preserves the template's nominal font size and enables text auto-fit
to keep longer pages within their text boxes. Different songs have separate title slides.

An optional `@` suffix on any hymn flag lists one-based Markdown page numbers
in singing order. Repeated numbers repeat a page; omitted pages are appended to
that song as hidden slides, preserving the complete resource. Without a suffix,
all pages appear once in their original order.

```text
--hymns=007_你的信實廣大@1,2,3,4,5,6,6
--hymns=342_主，我願像祢@2,1,2,3,4,9,10
```

After reviewing the service flags, run `make slides SUNDAY=YYYY-MM-DD`.
No source Keynote file or post-generation lyric replacement script is needed.
To create the matching `.key`, open the generated PPTX in Keynote and save it;
verify that skipped slides remain skipped and text auto-shrinking is enabled.

#### PPT轉純文本

```bash
$ make pptx_to_text PPTX=processed/mvccc/聖哉聖哉聖哉.pptx
uv run python mvccc/slides.py --extract_only --pptx processed/mvccc/聖哉聖哉聖哉.pptx
01 [['聖哉聖哉聖哉'], ['聖哉聖哉聖哉 聖哉是我主', '聖哉聖哉聖哉 聖哉惟有主', '祂是全能奇妙 愛四面環繞', '聖哉聖哉聖哉 聖哉是我主']]
```

### 聖經按章節範圍查找

```bash
$ make scripture VERSES="羅馬書12：1-2"
uv run python -m bible.scripture --bible_citations 羅馬書12：1-2
羅馬書12:1-2
  1 所以弟兄們、我以　神的慈悲勸你們、將身體獻上、當作活祭、是聖潔的、是　神所喜悅的．你們如此事奉、乃是理所當然的。
  2 不要效法這個世界．只要心意更新而變化、叫你們察驗何為　神的善良、純全可喜悅的旨意。
```

## 教會聖詩 Hymns for God's People

* https://www.izanmei.cc/songbook/hymns-for-gods-people.html
* http://www.hoc5.net/service/hymn0/002.htm
* http://mvcccit.org/Legacy/chinese/?content=it/song.htm
