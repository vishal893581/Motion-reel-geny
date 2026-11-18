const { chromium } = require('playwright-core');
const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');

(async () => {
  const theme = process.argv[2] || 'royal_indigo';
  const timelineData = JSON.parse(fs.readFileSync('timeline.json', 'utf8'));
  const duration = timelineData.total_duration;
  console.log(`Recording real-time motion video for ${duration}s...`);

  let html = fs.readFileSync('template.html', 'utf8');
  html = html.replace(/@import url\([^)]+\);/g, '');
  fs.writeFileSync('template_fast.html', html);

  const browser = await chromium.launch({
    executablePath: '/usr/bin/google-chrome',
    args: [
      '--no-sandbox',
      '--disable-dev-shm-usage',
      '--kiosk',
      '--window-size=1080,1920',
      '--window-position=0,0',
      '--autoplay-policy=no-user-gesture-required'
    ]
  });

  const context = await browser.newContext({ viewport: { width: 1080, height: 1920 } });
  const page = await context.newPage();
  await page.goto('file://' + path.resolve('template_fast.html'), { waitUntil: 'load' });
  await page.evaluate(({ data, th }) => {
    window.setTheme(th);
    window.initTimeline(data);
  }, { data: timelineData, th: theme });

  // Direct X11 virtual screen capture via FFmpeg (Zero screenshot bottleneck)
  const ffmpeg = spawn('ffmpeg', [
    '-y',
    '-f', 'x11grab',
    '-video_size', '1080x1920',
    '-framerate', '30',
    '-i', ':99',
    '-i', 'final_audio.m4a',
    '-t', String(duration),
    '-c:v', 'libx264',
    '-preset', 'veryfast',
    '-crf', '19',
    '-pix_fmt', 'yuv420p',
    '-c:a', 'aac',
    '-b:a', '192k',
    'final_reel.mp4'
  ]);

  // Play GSAP timeline smoothly in real-time
  await page.evaluate(() => window.masterTL.play(0));

  await new Promise((resolve) => ffmpeg.on('close', resolve));
  await browser.close();
  console.log('Viral Reel Recorded Successfully!');
})();
