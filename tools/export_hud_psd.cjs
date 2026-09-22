// Art handoff only. Reads runtime SVGs; never rewrites game assets or screens.
// Usage: node tools/export_hud_psd.cjs <new-output-folder>
const fs = require('fs');
const path = require('path');
const assert = require('assert/strict');
const deps = 'E:/ChatGPT/Temp/rememorial-psd-export/node_modules';
const { Resvg } = require(path.join(deps, '@resvg/resvg-js'));
const { DOMParser, XMLSerializer } = require(path.join(deps, '@xmldom/xmldom'));
const { writePsdBuffer, readPsd, initializeCanvas } = require(path.join(deps, 'ag-psd'));
const sharp = require('C:/Users/19512/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp');
const root = path.resolve(__dirname, '..');
const source = path.join(root, 'game/gui/hud_flat');
const outputArgument = process.argv.slice(2).find(arg => !arg.startsWith('--'));
const out = path.resolve(outputArgument || path.join(root, 'art_exports/HUD_2560x1440_20260919'));
const psdPath = path.join(out, 'ReMemorial_HUD_2560x1440.psd');
if (fs.existsSync(psdPath) && !process.argv.includes('--overwrite')) throw new Error('Output PSD already exists. Choose a new folder to protect painted work.');
const W = 2560, H = 1440;
const manifest = [];
let layerId = 0;
const serializer = new XMLSerializer();
const fontOptions = { loadSystemFonts: false, fontFiles: [path.join(root, 'game/fonts/source/HuiwenMincho.otf')], defaultFontFamily: 'Huiwen-mincho' };
initializeCanvas(() => { throw new Error('Export uses RGBA buffers, not Canvas.'); },
    (width, height) => ({ width, height, data: new Uint8ClampedArray(width * height * 4) }));

function svgParts(name) {
    const xml = fs.readFileSync(path.join(source, name + '.svg'), 'utf8');
    const element = new DOMParser().parseFromString(xml, 'image/svg+xml').documentElement;
    const nodes = Array.from(element.childNodes).filter(n => n.nodeType === 1);
    return { xml, width: +element.getAttribute('width'), height: +element.getAttribute('height'),
        viewBox: element.getAttribute('viewBox'),
        defs: nodes.filter(n => n.tagName === 'defs').map(n => serializer.serializeToString(n)).join(''),
        parts: nodes.filter(n => n.tagName !== 'defs').map(n => serializer.serializeToString(n)) };
}
function svg(width, height, content) {
    return `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}">${content}</svg>`;
}
function group(name, bottomToTop, hidden = false) {
    return { name, children: bottomToTop.slice().reverse(), hidden, opened: false, blendMode: 'pass through' };
}
async function pngLayer(name, png, left, top, meta = {}) {
    const { data, info } = await sharp(png).ensureAlpha().raw().toBuffer({ resolveWithObject: true });
    const id = ++layerId;
    const file = String(id).padStart(3, '0') + '_' + name.replace(/[<>:"/\\|?*\s]/g, '_') + '.png';
    fs.writeFileSync(path.join(out, 'layers_png', file), png);
    manifest.push({ id, name, file: 'layers_png/' + file, x: left, y: top, width: info.width, height: info.height, ...meta });
    return { name, id, left, top, imageData: { width: info.width, height: info.height, data: new Uint8ClampedArray(data) } };
}
async function svgLayer(name, xml, left, top, meta = {}) {
    const rendered = new Resvg(xml, { font: fontOptions }).render();
    return pngLayer(name, rendered.asPng(), left, top, meta);
}
async function asset(name, label, x, y, options = {}) {
    const a = svgParts(name);
    const chunks = options.labels ? a.parts.map((p, i) => ({ body: p, label: options.labels[i] || `部件 ${i + 1}` })) : [{ body: a.parts.join(''), label }];
    const layers = [];
    for (const c of chunks) {
        let width = a.width, height = a.height;
        if (options.size) {
            [width, height] = options.size;
        }
        // Render vector paths using their authored viewBox at native QHD size.
        // Each separated part retains the full original canvas and its alignment.
        let body = `<svg width="${width}" height="${height}" viewBox="${a.viewBox}">${a.defs + c.body}</svg>`;
        if (options.rotatePhoto) {
            const angle = 3 * Math.PI / 180;
            const rotatedWidth = Math.ceil(width * Math.cos(angle) + height * Math.sin(angle));
            const rotatedHeight = Math.ceil(height * Math.cos(angle) + width * Math.sin(angle));
            body = `<g transform="translate(${(rotatedWidth - width) / 2} ${(rotatedHeight - height) / 2}) rotate(-3 ${width / 2} ${height / 2})">${body}</g>`;
            width = rotatedWidth; height = rotatedHeight;
        }
        if (options.cropWidth) width = options.cropWidth;
        layers.push(await svgLayer(c.label, svg(width, height, body), x, y,
            { source: `source_svg/${name}.svg`, sourceSize: [a.width, a.height], state: options.state || 'default', note: options.note || '' }));
    }
    return group(label, layers, options.hidden || false);
}
function escapeXml(text) { return text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;'); }
async function textGuide(text, x, y, width, size, options = {}) {
    const lines = text.split('\n');
    const lineHeight = size + 11;
    const height = lines.length * lineHeight + 11;
    const anchor = options.align === 'right' ? 'end' : options.align === 'center' ? 'middle' : 'start';
    const tx = anchor === 'end' ? width - 2 : anchor === 'middle' ? width / 2 : 2;
    const fill = options.color || '#f3eee3';
    const stroke = options.outline ? 'stroke="#292923" stroke-width="1" paint-order="stroke"' : '';
    const body = lines.map((line, i) => `<text x="${tx}" y="${size + i * lineHeight}" text-anchor="${anchor}" font-family="Huiwen-mincho" font-size="${size}" fill="${fill}" ${stroke}>${escapeXml(line)}</text>`).join('');
    const layer = await svgLayer('文字参考_' + lines[0], svg(width, height, body), x, y, { note: 'Raster position guide only; runtime text remains live RenPy text.' });
    layer.protected = { composite: true, position: true };
    return layer;
}
function visibleLeaves(topToBottom, inheritedHidden = false) {
    const result = [];
    for (const node of topToBottom.slice().reverse()) {
        if (inheritedHidden || node.hidden) continue;
        if (node.children) result.push(...visibleLeaves(node.children));
        else result.push(node);
    }
    return result;
}
async function composite(children) {
    const inputs = visibleLeaves(children).map(l => ({ input: Buffer.from(l.imageData.data),
        raw: { width: l.imageData.width, height: l.imageData.height, channels: 4 }, left: l.left, top: l.top }));
    return sharp({ create: { width: W, height: H, channels: 4, background: '#00000000' } }).composite(inputs).raw().toBuffer();
}
async function main() {
    for (const folder of ['layers_png', 'assets_png', 'source_svg', 'reference']) fs.mkdirSync(path.join(out, folder), { recursive: true });
    fs.cpSync(source, path.join(out, 'source_svg'), { recursive: true });
    const svgFiles = fs.readdirSync(source).filter(n => n.endsWith('.svg'));
    for (const file of svgFiles) {
        const rendered = new Resvg(fs.readFileSync(path.join(source, file)), { font: { loadSystemFonts: false } }).render();
        fs.writeFileSync(path.join(out, 'assets_png', file.replace('.svg', '.png')), rendered.asPng());
    }

    const page = await asset('notebook_page', '纸页与纯色封皮', 53, 1056,
        { labels: ['封皮_纯色', '下层纸边', '中层纸边', '主纸面_质感绘制区'] });
    const tabs = [];
    const icons = ['article', 'eye-slash', 'arrows-clockwise', 'fast-forward', 'sliders-horizontal'];
    const captions = ['历史', '隐藏 UI', '自动', '快进', '设置'];
    const tabPositions = [1931, 2037, 2144, 2251, 2357];
    for (let i = 0; i < icons.length; i++) {
        const states = [];
        for (const state of ['idle', 'hover', 'selected']) {
            const tab = await asset(`dialogue_${icons[i]}_${state}`, `${state}_${captions[i]}`, tabPositions[i], state === 'hover' ? 971 : 1003,
                { labels: ['纸片后缘', '纸片底色', '纸片轮廓', '功能图标_待用户重绘', '开启状态短线'], hidden: state !== 'idle', state });
            if (state === 'hover') tab.children.unshift(await textGuide(captions[i], tabPositions[i], 1035, 96, 21, { align: 'center', color: '#292923' }));
            states.push(tab);
        }
        tabs.push(group(captions[i], states));
    }
    const photo = await asset('photo_mount', '人物照片底托_-3度', 139, 1083,
        { labels: ['照片底托后缘', '照片白边', '照片待绘占位'], rotatePhoto: true });
    const dialogue = group('01 对话框（页签在纸后）', [
        group('功能页签（一次仅开一种状态）', tabs), page, photo,
        await asset('photo_clip', '照片别针', 299, 1072),
        await svgLayer('姓名下细分隔线', svg(1707, 1, '<rect width="1707" height="1" fill="#a59e90"/>'), 384, 1152),
        await asset('play_ink', '继续_默认', 2389, 1307, { size: [64, 64] }),
        await asset('play_hover', '继续_悬停（替换默认）', 2389, 1307, { size: [64, 64], hidden: true, state: 'hover' }),
    ]);

    const clockStates = [];
    for (const mode of ['day', 'night']) {
        const parts = [];
        for (let i = 0; i < 4; i++) parts.push(await asset(`digit_${mode}_${'1530'[i]}`, `数字${i + 1}_示例15点30`, 64 + [72, 139, 232, 299][i], 107, { size: [64, 85], state: mode }));
        parts.push(await asset(`colon_${mode}`, '冒号', 269, 107, { size: [19, 85], state: mode }));
        const color = mode === 'night' ? '#cd5047' : '#f3eee3';
        parts.push(await textGuide('8月18日', 91, 59, 187, 32, { color }));
        parts.push(await textGuide('周五', 389, 59, 96, 32, { align: 'right', color }));
        parts.push(await textGuide('第1天', 362, 216, 123, 29, { align: 'right', color }));
        clockStates.push(group(`${mode}_时间为示例`, parts, mode === 'night'));
    }
    const clock = group('02 电子闹钟', [
        await asset('clock_case', '外壳', 64, 43, { labels: ['外壳背层', '浅色边框', '深色屏面', '内圈细线'] }),
        ...clockStates,
        group('轮次孔_三种状态样本（非实际轮序）', await Promise.all(['past', 'current', 'future'].map((state, i) =>
            asset(`hole_${state}`, `${state}_孔位示例`, 88 + 25 * i, 220, { state: 'reference' }))), true),
    ]);
    const meters = group('03 数值条与预留圆圈', [
        await asset('neuron', '神经元', 544, 32, { labels: ['胞体与树突', '蓝色胞核'] }),
        await asset('mood_track', 'Mood色带', 635, 85, { labels: ['浅色外轨', '蓝到红色带'] }),
        await asset('needle', 'Mood菱形游标_数值示例', 915, 76, { labels: ['游标外缘', '浅色半面', '深色半面'] }),
        await asset('lightning_track', '精力底条', 576, 171, { labels: ['底条', '闪电外缘', '绿色闪电', '空槽', '闪电与条连接'] }),
        await asset('lightning_fill', '精力填充_2比6示例', 576, 171, { cropWidth: 224, note: 'Current display crop; paint the full source asset in assets_png/lightning_fill.png, not this partial crop.' }),
        await asset('needle', '精力菱形游标_数值示例', 787, 180),
        await asset('heart_reserved', '生命值预留圈', 1163, 163, { labels: ['圆圈', '心形'] }),
        await asset('star_reserved', '魔力预留圈', 1280, 163, { labels: ['圆圈', '星形'] }),
        await asset('lightning_fill', '精力完整填充素材（绘制此层，默认隐藏）', 576, 171,
            { labels: ['底条', '闪电外缘', '绿色闪电', '完整绿色填充', '闪电与条连接'], hidden: true, state: 'full-template' }),
    ]);
    const navIcons = ['pill', 'device-mobile', 'backpack', 'dice-five', 'user-square'];
    const navCaptions = ['药盒', '手机', '背包', '骰组', '人物'];
    const navigation = [];
    for (let i = 0; i < navIcons.length; i++) navigation.push(group(navCaptions[i], [
        await asset(navIcons[i] + '_idle', '默认图标', 1700 + 171 * i, 48),
        await asset(navIcons[i] + '_hover', '素材库悬停配色（非当前导航运行态）', 1700 + 171 * i, 48, { hidden: true, state: 'library-variant' }),
        await svgLayer('运行态悬停淡色覆盖（默认隐藏）', svg(128, 160, '<rect width="128" height="160" fill="#f3eee3" fill-opacity=".0941176"/>'), 1684 + 171 * i, 43),
    ]));
    for (const item of navigation) item.children[0].hidden = true;

    const guideText = [];
    for (let i = 0; i < 5; i++) guideText.push(await textGuide(navCaptions[i], 1684 + 171 * i, 155, 128, 35, { align: 'center', outline: true }));
    for (const [text, y, size] of [['主线', 363, 40], ['主线排版测试', 432, 32], ['支线', 507, 40], ['支线排版测试一', 576, 32], ['支线排版测试二', 637, 32], ['全部任务', 712, 32]])
        guideText.push(await textGuide(text, 64, y, 331, size, { outline: true }));
    guideText.push(await textGuide('状态', 2176, 363, 320, 40, { align: 'right', outline: true }));
    guideText.push(await textGuide('状态排版测试', 2176, 432, 320, 32, { align: 'right', outline: true }));
    guideText.push(await textGuide('弗洛', 384, 1078, 293, 51, { color: '#292923' }));
    guideText.push(await textGuide('界面排版测试。左、中、右三个人物同时出现时，顶部保留数值和功能入口，两侧留出\n任务与状态的位置。', 384, 1173, 1707, 43, { color: '#292923' }));
    const text = group('05 动态文字位置参考（像素层，出素材时关闭）', guideText);

    const refFile = path.join(root, 'tmp/hud_qhd/2560x1440/day.png');
    const refMetadata = await sharp(refFile).metadata();
    assert.equal(refMetadata.width, W); assert.equal(refMetadata.height, H);
    const refPng = fs.readFileSync(refFile);
    fs.writeFileSync(path.join(out, 'reference/approved_runtime.png'), refPng);
    const reference = await pngLayer('已通过实机截图_仅对照_不要导出', refPng, 0, 0, { note: 'Reference only; contains scene and placeholder sprites. Not a flattened UI deliverable.' });
    reference.hidden = true;
    reference.protected = { composite: true, position: true };
    const backdrop = await svgLayer('预览底色_不属于UI', svg(W, H, '<rect width="2560" height="1440" fill="#656560"/>'), 0, 0);
    backdrop.hidden = true;
    const children = [text, group('04 右上功能入口', navigation), meters, clock, dialogue, reference, backdrop];
    const merged = await composite(children);
    const imageData = { width: W, height: H, data: new Uint8ClampedArray(merged) };
    const guides = [...[53, 64, 80, 139, 331, 384, 512, 576, 640, 1365, 1684, ...tabPositions, 2091, 2453, 2480, 2496, 2507].map(location => ({ location, direction: 'vertical' })),
        ...[43, 101, 205, 267, 363, 971, 1003, 1067, 1078, 1152, 1173, 1307, 1371, 1382].map(location => ({ location, direction: 'horizontal' }))];
    const psd = { width: W, height: H, children, imageData, imageResources: { gridAndGuidesInformation: { guides },
        resolutionInfo: { horizontalResolution: 72, horizontalResolutionUnit: 'PPI', widthUnit: 'Inches', verticalResolution: 72, verticalResolutionUnit: 'PPI', heightUnit: 'Inches' } } };
    fs.writeFileSync(psdPath, writePsdBuffer(psd, { noBackground: true, generateThumbnail: false, trimImageData: false }));
    const raw = { width: W, height: H, channels: 4 };
    await sharp(merged, { raw }).png().toFile(path.join(out, 'HUD_transparent.png'));
    await sharp(merged, { raw }).flatten({ background: '#656560' }).png().toFile(path.join(out, 'HUD_preview.png'));
    fs.writeFileSync(path.join(out, 'layer_positions.json'), JSON.stringify({ canvas: [W, H], units: 'px; origin top-left', layers: manifest }, null, 2));

    // Round-trip actual pixels, layer offsets, guides and hidden states.
    const read = readPsd(fs.readFileSync(psdPath), { useImageData: true, skipThumbnail: true });
    assert.equal(read.width, W); assert.equal(read.height, H);
    let verified = 0;
    function check(a, b) {
        assert.equal(a.length, b.length);
        a.forEach((layer, i) => {
            assert.equal(layer.name, b[i].name);
            assert.equal(Boolean(layer.hidden), Boolean(b[i].hidden));
            if (layer.children) check(layer.children, b[i].children);
            else {
                assert.equal(layer.left, b[i].left); assert.equal(layer.top, b[i].top);
                assert.ok(Buffer.from(layer.imageData.data).equals(Buffer.from(b[i].imageData.data)), `Layer pixels changed: ${layer.name}`);
                verified++;
            }
        });
    }
    check(children, read.children);
    const rereadComposite = await composite(read.children);
    assert.ok(rereadComposite.equals(merged), 'Compositing reloaded PSD layers must reproduce the PNG exactly.');
    assert.equal(read.imageResources.gridAndGuidesInformation.guides.length, guides.length);
    fs.writeFileSync(path.join(out, 'export_verification.txt'), `Canvas: ${W}x${H}\nIndependent pixel layers verified: ${verified}\nOriginal SVG / PNG assets: ${svgFiles.length}\nGuides: ${guides.length}\nPSD round-trip: all layer pixels, positions, names, visibility and recomposited appearance match exactly.\nPhotoshop application opening has not been tested on this host.\n`);
    console.log(JSON.stringify({ psd: psdPath, layers: verified, assets: svgFiles.length, bytes: fs.statSync(psdPath).size, status: 'verified' }, null, 2));
}
main().catch(error => { console.error(error); process.exitCode = 1; });
