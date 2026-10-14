# Who Am I? — free two-player character game

A ready-to-host, mobile-friendly, two-player guessing game. No paid AI model, paid image API, native app, or paid hosting is required. Built as plain HTML/CSS/JavaScript with the Firebase Realtime Database **Spark (free) plan** for room synchronization.

**Delivered in this starter:** 668 fictional/real characters from 35+ groups, 171 defined traits, 91 links meeting the initial broadness rules, independent private display cards, a room code + invitation URL, auto-selected links and characters, per-round image lookup, manual picture replacement, responsive design, a one-device demo, and tests.

**Status:** Application source complete and core pairing tests pass locally. **The multiplayer service is not active until you add your own free Firebase configuration and publish the site.** Actual Firebase/phone-to-phone connectivity has not been end-to-end tested in this environment.

## 1. Try the preview on a computer (no Firebase account needed)

Unzip the project. Serve the extracted folder over HTTP; opening `index.html` directly from `file://` will usually not allow its data file to load.

```sh
cd guess-the-character
python3 -m http.server 8000
```

Open `http://localhost:8000` and choose **Try a one-device preview**. The preview shows both players' answers on one screen *deliberately*. The production room view only reads the current device's private display card.

You can skip local testing and directly deploy the repository if preferred.

## 2. Set up Firebase — free Spark plan, no credit card

1. Visit https://console.firebase.google.com/ and create a project. Choose **Spark / No-cost**, not Blaze. You can skip Analytics.
2. Inside the project, go to **Build → Authentication → Sign-in method**, enable **Anonymous**, and save.
3. Go to **Build → Realtime Database** and **Create database**. Select a region. Choose **Locked mode** when offered.
4. In the database's **Rules** tab, **replace the entire rules text** with the contents of `database.rules.json`, then **Publish**. This is essential: otherwise the two-player private-card paths will be blocked or exposed.
5. Go to **Project settings → General → Your apps**, register a **Web app** (`</>` icon), and copy the Firebase `firebaseConfig` fields into `firebase-config.js`. Also fill in the `databaseURL` shown at the top of the Realtime Database page if it is missing.
6. Keep the project on Spark. The website needs **Realtime Database** and **Anonymous Authentication** only. No Cloud Functions, Cloud Storage, Vertex AI, generative AI, premium Google Cloud services, or billing account is needed.

A typical configuration looks like:

```js
export const firebaseConfig = {
  apiKey: 'YOUR_BROWSER_API_KEY',
  authDomain: 'your-project.firebaseapp.com',
  databaseURL: 'https://your-project-default-rtdb.REGION.firebasedatabase.app',
  projectId: 'your-project',
  appId: '1:000000000:web:example'
};
```

These are **client Firebase settings**, not a server-side secret. Access control comes from the installed database rules. Never put a service-account private key into this project.

If authentication complains about an unauthorised domain, open **Firebase Authentication → Settings → Authorized domains** and add your GitHub Pages domain (usually `YOUR-USERNAME.github.io`).

## 3. Host on GitHub Pages — free

1. Create a **public** GitHub repository called, for example, `guess-the-character`.
2. Upload the **contents** of this folder to the **root of the repository**, not to a nested folder. `index.html` should be at repository root.
3. Go to **Repository settings → Pages → Build and deployment**. Set **Deploy from a branch**, branch `main`, folder `/ (root)`, then save.
4. Once published, open the Pages URL given by GitHub, usually `https://YOUR-USERNAME.github.io/guess-the-character/`.
5. On phone one, press **Create game room**. On phone two, open the invitation link or type the six-character room code. The game automatically starts its first round after the second player joins.

Because the website uses paths relative to its own root, it works both at domain root and in the `/<repository>/` GitHub Pages subdirectory. It also works on tablets and desktop browsers.

## Playing

- Your device shows **the character your opponent is trying to guess**, not your own character.
- Both see the same shared link. Ask yes/no questions **aloud** and answer each other's questions.
- **Pass the turn** changes the shared turn indicator. **I guessed my character** marks the corresponding player as done.
- **New characters & link** starts a completely new round. Player 2's button requests it from the host's online browser; Player 1's button starts it immediately.
- **Fix image** opens a direct-image-URL override saved locally to the current browser and reflected on your private display card. If an image is blocked or missing, use the provided image-search link to find an alternative. External sites may block direct image embedding.
- A player needs the same browser/profile to return to the same seat after a reload. Clearing site data or reinstalling the browser deletes the anonymous sign-in; create a fresh room if you lose your seat.

## How round generation actually works

This version **does not pretend that an unlimited AI character generation service is free**. The source catalogue contains manually curated character records with many traits per record.

1. Pick a tag shared by **at least 12 entries from at least four separate people/franchises**. At runtime the game also requires enough candidates on each side after splitting stories into two sets.
2. Weight less-common links somewhat more heavily and avoid reusing recent links.
3. Split franchises (and individual real people) using a per-round hash, guaranteeing the two assigned characters are drawn from *different works or real people*.
4. Each browser independently selects its **opponent's** character from its own half, checking the recorded traits and trying to retrieve an actual usable image. Only this selected card is stored in the selecting browser's Firebase-protected path.
5. The site never downloads the other seat's private card. A determined technical user could still manipulate open-source client code or work out possibilities from the publicly available data; this is **casual-play privacy**, not a cryptographic commitment protocol.

A shared trait with a large eligible pool makes the game less easily deducible. A large pool and cross-work restriction are safeguards but **not a guarantee** that a clue is perfectly balanced, subjective-free, or equally difficult for everyone.

## How to expand the database / improve individual traits

The catalogue is generated from `scripts/build_catalog.py` and `data/custom_characters.json`.

- For built-in entries, edit the rows in `scripts/build_catalog.py`. Each row contains `Character name | Wikipedia article title | space-separated trait identifiers`. The group declaration supplies format/context traits (which are also included in the character record).
- Trait definitions and their human-readable clue wording are in `LINKS` at the start of that Python file. Add a new entry there if you want a new kind of relationship, then tag enough characters from distinct works to make it available.
- To add obscure people, side characters, or particular adaptations **without modifying the seed**, add objects to the `data/custom_characters.json` array. A sample entry is below. `work` can be an explicit adaptation such as `2017 live-action film`; `article` should match the most specific Wikipedia article available. If you have permission to embed a specific image, you can also include its direct `imageUrl` and original `imageSource` link.

```json
[
  {
    "name": "Your character name",
    "work": "Film, game, book, year and/or particular adaptation",
    "medium": "animated film",
    "kind": "fictional",
    "article": "Exact English Wikipedia article title",
    "tags": ["glasses", "detective", "student", "school", "friendship", "mystery", "fictional", "film", "animation", "hero", "young", "family"],
    "imageUrl": "https://example.org/optional-image.png",
    "imageSource": "https://example.org/image-license-and-credits"
  }
]
```

Remove `imageUrl` and `imageSource` entirely if not using them. All tags must exist in `LINKS`. Traits are not filled by speculative AI: you must verify each tag's accuracy, particularly for specific adaptations. Then run:

```sh
python3 scripts/build_catalog.py
node --test tests/core.test.mjs
```

Commit/upload the new `data/catalog.json` to GitHub to publish the expanded list. Other phones will pick up the new catalogue after refreshing the website. Avoid changing the catalogue mid-round; both phones should be on the same revision.

**The provided catalogue is a substantial starting set, not an exhaustive, continually updated universe.** Side characters are included, but there are finite entries; adding obscure characters and tagging them responsibly takes human review. The generator intentionally avoids unverified open-ended AI claims.

## Images, copyright and limitations

The app uses Wikipedia PageImages thumbnails, including images marked non-free by Wikipedia when available, and only treats a direct image URL as valid if it loads in the browser. Some articles have no suitable image or have a franchise/movie picture instead of a precise character portrait. If no image resolves, the name still appears and you can use **Fix image**. An image's existence on Wikipedia or Google does **not** grant unrestricted permission to reuse it on another public website. Respect licence, attribution, personality, and hotlinking restrictions. Images on Wikimedia Commons have individual licences; some Wikipedia images are non-free and used there under Wikipedia's local policy, which is **not transferable** to your hosted site.

Your custom picture URL lives in Firebase on **your own private picker path** and in browser storage. It is not uploaded to our server (there is no custom server).

Firebase Spark quotas and GitHub Pages usage rules can change; if either free service stops serving requests, the game may stop working rather than silently upgrading and charging you. Remain on Spark, do not add billing, and do not convert the app into a high-traffic public service.

## Files

- `index.html`, `styles.css`: mobile-responsive interface.
- `app.js`: Firebase room state, image retrieval, turn control, demo.
- `game-core.mjs`: pure round selection and story/character partitioning.
- `firebase-config.js`: fill in browser config once.
- `database.rules.json`: **required** private database security rules.
- `data/catalog.json`: generated catalogue loaded by browser.
- `data/custom_characters.json`: optional additional records.
- `scripts/build_catalog.py`: catalogue and link-definition source; creates `data/catalog.json`.
- `tests/core.test.mjs`: offline tests of catalogue structure, privacy rule shape, and pair constraints.

## Notes on security

Firebase database security rules are evaluated on the server. `meta` is readable to authenticated browsers that know/guess the 6-character room ID. Individual private cards are isolated to the Firebase anonymous UID assigned to the matching seat. Do not delete or loosen the rules. This project does not currently expire or delete old game rooms; very small personal use is within free-tier storage, but accumulated abandoned rooms can be cleared manually from the Firebase console.
