const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');

(async () => {
  const timelineData = JSON.parse(fs.readFileSync('timeline.json', 'utf8'));
  const fps = 60;
  const totalFrames = Math.ceil(timelineData.total_duration * fps);

  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
  await page.goto('file://' + path.resolve('template.html'), { waitUntil: 'networkidle' });
  await page.evaluate((data) => window.initTimeline(data), timelineData);

  // Pipe raw PNG frames directly into FFmpeg (Zero disk bloat, super fast)
  const ffmpeg = spawn('ffmpeg', [
    '-y',
    '-f', 'image2pipe',
    '-vcodec', 'png',
    '-r', String(fps),
    '-i', '-',
    '-i', 'final_audio.m4a',
    '-c:v', 'libx264',
    '-preset', 'medium',
    '-crf', '18',
    '-pix_fmt', 'yuv420p',
    '-c:a', 'aac',
    '-b:a', '192k',
    '-shortest',
    'final_reel.mp4'
  ]);

  ffmpeg.stderr.on('data', (d) => process.stderr.write(d));

  for (let frame = 0; frame < totalFrames; frame++) {
    const timeSec = frame / fps;
    await page.evaluate((t) => window.masterTL.seek(t, false), timeSec);
    const buffer = await page.screenshot({ type: 'png' });
    ffmpeg.stdin.write(buffer);
  }

  ffmpeg.stdin.end();
  await new Promise((resolve) => ffmpeg.on('close', resolve));
  await browser.close();
  console.log('60FPS Motion Reel Rendered Successfully!');
})();
