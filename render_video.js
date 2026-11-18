const { chromium } = require('playwright-core');
const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');

(async () => {
  const theme = process.argv[2] || 'royal_indigo';
  const timelineData = JSON.parse(fs.readFileSync('timeline.json', 'utf8'));
  const fps = 30;
  const totalFrames = Math.ceil(timelineData.total_duration * fps);

  const browser = await chromium.launch({
    executablePath: '/usr/bin/google-chrome',
    args: ['--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu']
  });

  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
  await page.goto('file://' + path.resolve('template.html'), { waitUntil: 'domcontentloaded' });
  await page.evaluate(({ data, th }) => {
    window.setTheme(th);
    window.initTimeline(data);
  }, { data: timelineData, th: theme });

  const ffmpeg = spawn('ffmpeg', [
    '-y',
    '-f', 'image2pipe',
    '-vcodec', 'mjpeg',
    '-r', String(fps),
    '-i', '-',
    '-i', 'final_audio.m4a',
    '-c:v', 'libx264',
    '-preset', 'veryfast',
    '-crf', '19',
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
    const buffer = await page.screenshot({ type: 'jpeg', quality: 92 });
    if (!ffmpeg.stdin.write(buffer)) {
      await new Promise((r) => ffmpeg.stdin.once('drain', r));
    }
    if (frame % 150 === 0) console.log(`Progress: ${frame}/${totalFrames} frames`);
  }

  ffmpeg.stdin.end();
  await new Promise((resolve) => ffmpeg.on('close', resolve));
  await browser.close();
  console.log('Viral Reel Rendered Successfully!');
})();
