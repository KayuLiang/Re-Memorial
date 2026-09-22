# Font Sources

ReMemorial uses separate UI and story font groups. Both retain the existing
Source Han Sans fallback. Font files are unmodified.

- `SourceHanSerifSC-SemiBold.otf` — 思源宋体 / Source Han Serif SC SemiBold
  - Location: `game/fonts/source-han-serif/SourceHanSerifSC-SemiBold.otf`
  - Version: 2.003 (release 2.003R)
  - Official project: https://github.com/adobe-fonts/source-han-serif
  - Download: https://raw.githubusercontent.com/adobe-fonts/source-han-serif/2.003R/OTF/SimplifiedChinese/SourceHanSerifSC-SemiBold.otf
  - License: SIL Open Font License 1.1; commercial use and software bundling allowed.
  - Full license: `game/fonts/source-han-serif/LICENSE.txt` (retain when distributing).
  - Use: current global UI, HUD, menus, tooltips and system documents.
  - Uses the actual SemiBold font file, not synthetic bold. Speaker names, dialogue
    and narration retain Huiwen; speaker names have no additional bold.
  - Previous Regular and Medium files are retained on disk but not used by runtime UI.
  - Chosen as a close commercial-use alternative to the supplied Song/Mincho reference;
    the reference's exact font has not been identified.

- `LXGWWenKaiScreen.ttf` — 霞鹜文楷屏幕阅读版 / LXGW WenKai Screen
  - Location: `game/fonts/lxgw-wenkai-screen/LXGWWenKaiScreen.ttf`
  - Version: v1.522
  - Official project: https://github.com/lxgw/LxgwWenKai-Screen
  - Release: https://github.com/lxgw/LxgwWenKai-Screen/releases/tag/v1.522
  - License: SIL Open Font License 1.1; commercial use and software bundling allowed.
  - Full license: `game/fonts/lxgw-wenkai-screen/OFL.txt` (retain when distributing).
  - Use: previous UI candidate; retained on disk, no longer used by runtime UI.

- `HuiwenMincho.otf`
  - Use: story dialogue, narration, restored speaker names and dialogue-history content.
  - Source page: https://www.fonthubs.com/fonts/huiwen-mincho
  - Download object: https://bucket.fonthubs.com/deac7179-5d56-41e1-8263-c53bc85380de.otf
  - Source page license note: Public Domain.

- `SourceHanSansLite.ttf`
  - Location: `game/SourceHanSansLite.ttf`
  - Use: fallback glyphs for both font groups.

No generated layered font is used by the current runtime configuration.
