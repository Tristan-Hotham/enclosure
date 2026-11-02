// QA: open index.html at desktop and phone widths, log console errors, take screenshots to qa/.
// Run from the study root with a static server (python3 -m http.server 8873; set PORT to change).
const { chromium } = require("playwright");
// MapLibre from a local npm copy (the CDN is not reachable from the build container); tiles and fonts are blocked here.
const ML = process.env.MAPLIBRE_DIST || "/tmp/ml/node_modules/maplibre-gl/dist";
const fs = require("fs");
(async () => {
  fs.mkdirSync("qa", { recursive: true });
  const b = await chromium.launch({ args: ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"] });
  const errs = [];
  // 1. graceful degradation: no MapLibre at all (CDN blocked)
  {
    const p = await b.newPage({ viewport: { width: 1280, height: 900 } });
    await p.route(/maplibre-gl|arcgisonline|googleapis|gstatic/, r => r.abort());
    p.on("pageerror", e => errs.push("nomap pageerror: " + e.message));
    await p.goto("http://localhost:" + (process.env.PORT || 8873) + "/index.html", { waitUntil: "load" });
    await p.waitForTimeout(1500);
    console.log("no maplibre:", await p.textContent("#loading"), "| charts:", await p.evaluate(() => document.querySelectorAll(".chart svg").length));
    await p.locator("#atlas").screenshot({ path: "qa/nomap_atlas.png" });
    await p.close();
  }
  for (const [nm, vw, vh] of (process.env.ONLY ? [[process.env.ONLY, process.env.ONLY === "phone" ? 390 : 1280, 900]] : [["desktop", 1280, 900], ["phone", 390, 844]])) {
    const p = await b.newPage({ viewport: { width: vw, height: vh }, deviceScaleFactor: nm === "phone" ? 2 : 1 });
    await p.route(/arcgisonline|googleapis|gstatic/, r => r.abort());
    await p.route(/maplibre-gl\.js$/, r => r.fulfill({ path: ML + "/maplibre-gl.js" }));
    await p.route(/maplibre-gl\.css$/, r => r.fulfill({ path: ML + "/maplibre-gl.css" }));
    p.on("console", m => { if (m.type() === "error" && !/ERR_FAILED|net::|Failed to fetch|AJAXError/.test(m.text())) errs.push(nm + ": " + m.text()); });
    p.on("pageerror", e => errs.push(nm + " pageerror: " + e.message));
    await p.goto("http://localhost:" + (process.env.PORT || 8873) + "/index.html", { waitUntil: "load" });
    for (let k = 0; k < 60 && !(await p.evaluate(() => !!window.map && document.getElementById("loading") === null)); k++) await p.waitForTimeout(500);
    console.log(nm, "map ready:", await p.evaluate(() => !!window.map && document.getElementById("loading") === null));
    await p.waitForTimeout(2000);
    await p.screenshot({ path: `qa/${nm}_top.png` });
    const shot = async (sel, f) => { await p.locator(sel).scrollIntoViewIfNeeded(); await p.waitForTimeout(700); await p.locator(sel).screenshot({ path: `qa/${nm}_${f}.png` }); };
    const drawn = async () => p.evaluate(() => map.queryRenderedFeatures({ layers: ["dots"] }).length);
    await shot("#atlas", "map");
    console.log(nm, "dots drawn (all):", await drawn());
    // year 1780, cumulative
    await p.evaluate(() => { const r = document.getElementById("yr"); r.value = 1780; r.dispatchEvent(new Event("input")); }); await p.waitForTimeout(900);
    console.log(nm, "dots to 1780:", await drawn(), "label:", await p.textContent("#yv")); await shot("#atlas", "map_1780");
    // play
    await p.click("#play"); await p.waitForTimeout(2200); await p.click("#play");
    console.log(nm, "after play:", await p.textContent("#yv"));
    // decade window in the war years
    await p.click('#modeRow [data-m="dec"]'); await p.evaluate(() => setYear(1812)); await p.waitForTimeout(900); await shot("#atlas", "map_1803_1812");
    await p.click('#modeRow [data-m="cum"]'); await p.evaluate(() => setYear(1850));
    // county choropleth
    await p.click('#viewRow [data-v="cty"]'); await p.waitForTimeout(1000); await shot("#atlas", "counties");
    await p.evaluate(() => pickCounty("Northamptonshire", true)); await p.waitForTimeout(1500); await shot("#atlas", "county_northants");
    await p.click('#viewRow [data-v="dots"]'); await p.click(".side .back").catch(() => {});
    // search and popup
    await p.fill("#q", "Elsdon"); await p.waitForTimeout(400); await p.keyboard.press("Enter"); await p.waitForTimeout(2200); await shot("#atlas", "search_elsdon");
    console.log(nm, "popup:", (await p.textContent(".maplibregl-popup-content").catch(() => "none")).slice(0, 140));
    // click a dot directly
    await p.click('#focusRow .btn:nth-child(3)'); await p.waitForTimeout(800);
    const pt = await p.evaluate(() => { const f = map.queryRenderedFeatures({ layers: ["dots"] })[0]; if (!f) return null; const q = map.project(f.geometry.coordinates); const r = map.getCanvas().getBoundingClientRect(); return [r.left + q.x, r.top + q.y]; });
    if (pt) { await p.locator("#map").scrollIntoViewIfNeeded(); await p.waitForTimeout(600); const pt2 = await p.evaluate(() => { const f = map.queryRenderedFeatures({ layers: ["dots"] })[0]; if (!f) return [0, 0]; const q = map.project(f.geometry.coordinates); const r = map.getCanvas().getBoundingClientRect(); return [r.left + q.x, r.top + q.y]; }); if (pt2[0]) await p.mouse.click(pt2[0], pt2[1]); await p.waitForTimeout(800);
      console.log(nm, "click popup:", (await p.textContent(".maplibregl-popup-content").catch(() => "none")).slice(0, 120)); await shot("#atlas", "click_popup"); }
    // layers panel
    await p.locator("#map").scrollIntoViewIfNeeded();
    await p.click(".lyrBtn"); await p.waitForTimeout(300);
    await p.evaluate(() => { for (const k of ["cnames", "hills"]) { const c = document.querySelector(`.lyrPanel [data-k="${k}"]`); c.checked = true; c.dispatchEvent(new Event("change")); } });
    await p.waitForTimeout(800); await shot("#map", "layers_panel");
    console.log(nm, "layers:", await p.evaluate(() => JSON.stringify({ hills: map.getLayoutProperty("hills", "visibility"), cty: map.getLayoutProperty("ctyline", "visibility"), labels: document.querySelectorAll(".townL,.ctyL").length })));
    await p.click(".lyrPanel .reset"); await p.click(".lyrBtn");
    await p.click('#focusRow .btn:nth-child(2)'); await p.waitForTimeout(800);
    for (const c of ["yearChart", "eraChart", "ctyChart", "ctyTable", "waveChart", "cenChart", "twiceChart"]) await shot("#" + c, c);
    if (nm === "phone") { await p.click("#theme"); await p.waitForTimeout(1500); await shot("#atlas", "dark_map"); await shot("#yearChart", "dark_year"); await p.click("#theme"); }
    await p.locator("#mapbox").scrollIntoViewIfNeeded(); await p.click(".mfs-btn"); await p.waitForTimeout(1500);
    console.log(nm, "fullscreen:", await p.evaluate(() => !!(document.fullscreenElement || document.querySelector(".mfs-fake"))), "map h:", await p.evaluate(() => document.getElementById("map").clientHeight));
    await p.screenshot({ path: `qa/${nm}_fullscreen.png` });
    await p.click(".mfs-btn"); await p.waitForTimeout(500);
    const ov = await p.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    console.log(nm, "horizontal overflow px:", ov);
    await p.close();
  }
  console.log("errors:", errs.length ? errs : "none");
  await b.close();
})();
