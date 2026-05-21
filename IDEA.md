Optimizing your font stack over @font-face requires looking past simple stylesheet declarations; you need to map out what is actually being rendered on the DOM versus what is just sitting dormant in your CSS.
Because most basic browser extensions (like WhatFont) only look at a single page element-by-element, you need specialized web crawlers and CSS auditing tools to handle site-wide aggregation.
The best tools and methods to achieve this, broken down from automated platforms to programmatic scraping, are detailed below.
1. Dedicated CSS & Font Crawlers
Apify's "Font Detector" & "CSS Stats Analyzer"
Apify has specialized cloud-based "Actors" (headless browser crawlers) built exactly for this purpose.
• How it works: You give it a starting URL, and it crawls the pages using headless Chrome. The Font Detector parses inline styles, external stylesheets, and actual font-rendering metrics.
• What it outputs: It spits out a structured JSON array comparing fontFamiliesInCss against actual web fonts loaded. This allows you to see if you have an @font-face rule pulling in a heavy .woff2 file that no HTML element on your site is actually calling.
Project Wallace / CSS Analytics
Project Wallace is a highly respected CSS code-quality tool that aggregates statistics on your selectors, colors, and typography.
• How it works: While primarily used by feeding it your build stylesheets, you can integrate its CLI or web hook into a site-crawler to map out font-family occurrences, specific font-weights used, and variations across your entire CSS footprint.
2. In-Browser "Site-Wide" CSS Auditing
If you don't want to spin up a cloud crawler, you can analyze the current state of a page (or sequential pages) right via developer tools or specialized extensions.
Chrome DevTools "CSS Overview" Panel
Chrome has a hidden gem built directly into its experimental/extra panels called CSS Overview.
• How to open it: Open DevTools (\text{F12}), click the three vertical dots (top right of DevTools) \rightarrow More tools \rightarrow CSS Overview.
• What it does: Click "Capture overview". It scans the live DOM and yields an aggregate report: • Colors: Every background, text, and border color used (and highlights contrast issues). • Typography: An exact aggregated list of every Font Family rendered on that page, broken down by how many times each specific combination of Font-Family + Weight + Line-Height appears. • Limitation: It operates page-by-page rather than clicking through your whole site automatically, but it is flawless for mapping actual DOM usage.
3. The Programmatic Approach (The "Perfect" Solution)
Pre-built crawlers sometimes miss fonts loaded dynamically via JavaScript font loaders (like Adobe Fonts or specific Google Font async snippets). If you want an ironclad, site-wide audit to optimize your @font-face load, writing a quick Node.js script using Puppeteer or Playwright is the industry standard.
You can write a simple script that crawls your sitemap, boots up a headless browser, and executes this snippet on every page to aggregate a master list:
// A snippet executed inside a Puppeteer crawl loop
const pageFonts = await page.evaluate(() => {
  const fonts = new Set();
  // Grab every element on the page
  const elements = document.querySelectorAll('*');
  
  elements.forEach(el => {
    // Get the computed style (what the browser actually resolves)
    const style = window.getComputedStyle(el);
    const fontFamily = style.getPropertyValue('font-family');
    const fontWeight = style.getPropertyValue('font-weight');
    
    if (fontFamily) {
      fonts.add(`${fontFamily.replace(/"/g, '')} (Weight: ${fontWeight})`);
    }
  });
  
  return Array.from(fonts);
});

How this optimizes your @font-face
By running a script like this across your site, you can compare the output to your CSS file:
1. Unused Weights: You might discover you are loading @font-face files for font-weight: 300 and font-weight: 900, but your aggregate site data shows only 400 and 700 are actually rendered. You can safely drop those @font-face declarations.
2. System Font Fallbacks: You can track if a custom web font is failing to load on certain legacy pages, forcing the browser to drop back to Arial or sans-serif natively.
Are you looking to plug this directly into a CI/CD build pipeline to prevent font-bloat automatically, or are you doing a one-time manual cleanup of a legacy site?Here are the strongest options for crawling a site and aggregating which font‑families (and other CSS rules) are actually rendered, ordered by how well they fit your @font‑face stack‑optimization goal.

## Purpose‑built CSS analyzers

- **Project Wallace** — the closest match for your use case. Point it at a URL (or paste raw CSS) and it produces aggregate stats on font-families, font-sizes, colors, units, selectors, specificity, complexity, @media, etc.. It also has a CLI/API (`@projectwallace/css-analyzer`) so you can run it across many crawled pages and merge results, which is what you'd want for a multi‑page site audit feeding back into a `@font-face` subset decision.[1]
- **CSS Stats Analyzer (Apify)** — a hosted crawler‑style actor that audits a webpage's CSS statistics including selectors, colors, specificity and file sizes. Because it's an Apify actor, you can wire it into a full‑site crawl and aggregate JSON output across URLs.[2]
- **analyze-css (macbre)** — open‑source Node library built as rules bound to a CSS parser; each rule emits metrics and "offenders" with details. Easy to combine with a crawler (e.g. Puppeteer/Playwright) and extend with custom rules for font‑family usage counts.[3]

## Tools that capture *rendered* fonts (not just declared)

This is the critical distinction for `@font-face` optimization — you want what the browser actually picked from the stack, not what was authored.

- **Chrome DevTools "Rendered font"** in the Computed pane reports the real font the browser used per element, including whether it came from network or local. Scriptable via Puppeteer/Playwright using the `CSS.getPlatformFontsForNode` CDP command — this is the right primitive to build your own crawler around.[4][5]
- **Firefox DevTools → Inspector → Fonts panel** lists all fonts actually used on the page plus the `@font-face` rules that defined them, and underlines the chosen family in the rule view. Firefox only fetches fonts that are actually used, so its network panel filtered to "Fonts" gives you a clean used‑set per page.[6][7]
- **Chrome DevTools CSS Overview / Coverage** — CSS Overview aggregates colors, fonts, media queries and unused declarations for a page, and Coverage reports unused CSS bytes. Per‑page only, but useful as a sanity check.[8][9]
- **Font Inspector** and **CSS Pully** Chrome extensions surface the *real* rendered font, colors, shadows and styles per element. Manual, not crawl‑scale.[10][11]

## Recommended pipeline for your goal

Given you want to trim a `@font-face` stack down to families that are actually rendered across the whole site:

1. Crawl with **Puppeteer or Playwright** (suggested in the Reddit thread for exactly this scenario).[8]
2. For every text node / representative element, call CDP `CSS.getPlatformFontsForNode` to record the *rendered* family and glyph count — this matches what DevTools' "Rendered font" shows.[5][4]
3. In parallel, run **Project Wallace's analyzer** on each page's CSS to aggregate declared font-families, colors, units and other rule statistics.[1]
4. Merge per‑page JSON into a site‑wide histogram: declared family → rendered family → glyph count → URLs. Anything declared in `@font-face` that never appears as a rendered family is a candidate for removal or subsetting.
5. Optionally cross‑check with Chrome's **Coverage** report to drop unused `@font-face` byte ranges as well.[9]

If you'd like, I can sketch a minimal Playwright + `CSS.getPlatformFontsForNode` script that emits a CSV of declared‑vs‑rendered font families per URL — would that be useful as a starting point?

Sources
[1] Online CSS Analyzer - Project Wallace https://www.projectwallace.com/analyze-css
[2] CSS Stats Analyzer — Website CSS Audit and Inspector - Apify https://apify.com/automation-lab/css-stats-analyzer
[3] macbre/analyze-css: CSS selectors complexity and ... - GitHub https://github.com/macbre/analyze-css
[4] How to tell if one of my website's fonts is being sourced from ... - Reddit https://www.reddit.com/r/web_design/comments/1eqafdi/how_to_tell_if_one_of_my_websites_fonts_is_being/
[5] Identify Fonts on Any Website Using Developer Tools (Chrome ... https://n8d.at/how-to-identify-the-font-rendered-in-your-browser/
[6] How to identify all weights of all fonts used on page/site https://stackoverflow.com/questions/23467432/how-to-identify-all-weights-of-all-fonts-used-on-page-site
[7] Know which of the font in a font-family was actually used https://devtoolstips.org/tips/en/see-which-font-was-used-in-font-family/
[8] Is there a tool that can crawl website to show what font was used ... https://www.reddit.com/r/webdev/comments/ty8jwy/is_there_a_tool_that_can_crawl_website_to_show/
[9] Coverage: Find unused JavaScript and CSS | Chrome DevTools https://developer.chrome.com/docs/devtools/coverage
[10] CSS Pully – Font & Color & Style Inspector - Chrome Web Store https://chromewebstore.google.com/detail/css-pully-%E2%80%93-font-color-st/fijjgmefkbbfhobbdeknhpblfpgggkec
[11] Font Inspector - Chrome Web Store https://chromewebstore.google.com/detail/font-inspector/ldanlnlkbcpglobchelebddfmjapiifd
[12] Analyze CSS selector performance during Recalculate Style events https://developer.chrome.com/docs/devtools/performance/selector-stats
[13] font-face is not working for CSS with correct format, generation, and ... https://stackoverflow.com/questions/69217114/font-face-is-not-working-for-css-with-correct-format-generation-and-directory
[14] Crawl budget optimization: Enhancing SEO efficiency | Blog - Senuto https://www.senuto.com/en/blog/crawl-budget/
[15] Automatically Find Trends in CSS, JavaScript and Lighthouse ... https://www.inovex.de/de/blog/automatically-scraping-the-web-to-find-trends-in-css-javascript-frameworks-and-lighthouse-performance/
