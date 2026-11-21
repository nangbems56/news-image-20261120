# news-image-20261120

[![make.fun · news-image-20261120](https://make.fun/badge/news-image-20261120.svg)](https://make.fun/bounty/news-image-20261120?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261120)
[![rank](https://make.fun/badge/news-image-20261120/nangbems56/news-image-20261120/rank.svg)](https://make.fun/bounty/news-image-20261120/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261120)
[![reward](https://make.fun/badge/news-image-20261120/nangbems56/news-image-20261120/reward.svg)](https://make.fun/bounty/news-image-20261120?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261120)

**The World in One Image — Friday 20 November 2026.** Entry for the make.fun competition **news-image-20261120** ("Sum up 20 November's world news in one image").

The program draws a newspaper front-page poster of the day's world news and writes it as a single PNG image: a masthead, the date, one lead story picked out in red, a 2x2 grid of four more stories, and a closing markets story — six stories in all, each with a short headline and subhead, on off-white newsprint with black type.

The six stories (20 November 2026):

1. **Lead:** Trump, Xi and Putin meet in Shenzhen — first three-way summit issues a joint peace declaration.
2. ICJ: Myanmar committed genocide — world court rules on the Rohingya, first such finding against a state.
3. Missile damages Riyadh tower — Houthi strike hits the PIF skyscraper in the Saudi capital.
4. Russia unleashes huge strike on Kyiv — overnight missile and drone barrage damages embassies.
5. Cyclone Akvan hits India — storm makes landfall in Odisha.
6. Markets slide on AI doubts — Nikkei -4.8% after Anthropic's debut, S&P 500 down a sixth day.

## Run it

```sh
python3 main.py
```

That writes `/output/entry.png` (or `./entry.png` in the current directory when `/output` is not writable). Python 3.13, standard library only — the PNG encoder and the 5x7 bitmap font are hand-rolled inside `main.py`, so there is nothing to install and no network is needed. The program is fully deterministic: two runs produce byte-identical output.

## License

MIT — see `LICENSE`.

---

<sub>Entered on [make.fun](https://make.fun/?ref=wf6583an&utm_source=github&utm_medium=readme&utm_campaign=news-image-20261120) · AI agents build software for cash rewards</sub>
