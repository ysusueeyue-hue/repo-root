const axios = require("axios");

function is_xhamster(url) {
  return url.toLowerCase().includes("xhamster");
}

// =====================================
// 🔥 THUMBNAIL
// =====================================
function extract_thumbnail(html) {
  let match = html.match(/<meta property="og:image" content="([^"]+)"/);
  if (match) return match[1];

  match = html.match(/<meta name="twitter:image" content="([^"]+)"/);
  if (match) return match[1];

  return null;
}

// =====================================
// 🔥 MAIN
// =====================================
exports.handler = async (event) => {
  const url = event.queryStringParameters?.url;

  if (!url) {
    return {
      statusCode: 400,
      body: JSON.stringify({ error: "URL required" }),
    };
  }

  try {
    if (is_xhamster(url)) {
      return await extract_xhamster(url);
    } else {
      return await extract_other(url);
    }
  } catch (e) {
    return {
      statusCode: 500,
      body: JSON.stringify({ error: e.toString() }),
    };
  }
};

// =====================================
// 🔥 XHAMSTER
// =====================================
async function extract_xhamster(url) {
  let html;

  for (let i = 0; i < 3; i++) {
    try {
      const res = await axios.get(url, {
        headers: {
          "User-Agent": "Mozilla/5.0",
          Referer: "https://xhamster.com/",
        },
        timeout: 20000,
      });
      html = res.data;
      break;
    } catch {
      await new Promise(r => setTimeout(r, 2000));
    }
  }

  if (!html) {
    return response({ error: "Failed" });
  }

  const thumb = extract_thumbnail(html);

  let links = new Set();

  let m3u8 = html.match(/https?:\/\/[^\s"'"]+\.m3u8[^\s"'"]*/g) || [];
  m3u8.forEach(l => links.add(l));

  let jsonLinks = html.match(/"url":"(https:[^"]+)"/g) || [];
  jsonLinks.forEach(l => {
    let clean = l.match(/https:[^"]+/)[0].replace(/\\\//g, "/");
    if (clean.includes(".m3u8")) links.add(clean);
  });

  if (links.size === 0) {
    let mp4 = html.match(/https?:\/\/[^\s"'"]+\.mp4[^\s"'"]*/g);
    if (mp4) {
      return response({
        thumbnail: thumb,
        video: mp4[0],
        type: "mp4",
      });
    }
    return response({ error: "No link" });
  }

  let link = Array.from(links)[0];

  let playlist = await axios.get(link).then(r => r.data);

  let base = link.split("/key=")[0];

  let qualities = ["144p", "240p", "480p", "720p", "1080p"];

  let found = {};

  for (let q of qualities) {
    let match = playlist.match(new RegExp(`(/key=.*${q}.*\\.m3u8)`));
    if (match) {
      found[q] = base + match[1];
    }
  }

  let final =
    found["720p"] ||
    found["480p"] ||
    found["240p"] ||
    found["144p"] ||
    Object.values(found)[0];

  return response({
    thumbnail: thumb,
    video: final,
    type: "m3u8",
  });
}

// =====================================
// 🔥 OTHER DOMAIN
// =====================================
async function extract_other(url) {
  let html;

  for (let i = 0; i < 3; i++) {
    try {
      const res = await axios.get(url, {
        headers: {
          "User-Agent": "Mozilla/5.0",
          Referer: "https://xhamster.com/",
        },
        timeout: 20000,
      });
      html = res.data;
      break;
    } catch {
      await new Promise(r => setTimeout(r, 2000));
    }
  }

  if (!html) return response({ error: "Failed" });

  const thumb = extract_thumbnail(html);

  let mp4 = html.match(/https?:\/\/[^\s"'"]+\.mp4[^\s"'"]*/g);
  if (mp4) {
    return response({
      thumbnail: thumb,
      video: mp4[0],
      type: "mp4",
    });
  }

  let links = new Set();

  let m3u8 = html.match(/https?:\/\/[^\s"'"]+\.m3u8[^\s"'"]*/g) || [];
  m3u8.forEach(l => links.add(l));

  let jsonLinks = html.match(/"url":"(https:[^"]+)"/g) || [];
  jsonLinks.forEach(l => {
    let clean = l.match(/https:[^"]+/)[0].replace(/\\\//g, "/");
    if (clean.includes(".m3u8")) links.add(clean);
  });

  if (links.size === 0) {
    return response({ error: "No video link found" });
  }

  let link = Array.from(links)[0];

  return response({
    thumbnail: thumb,
    video: link,
    type: "raw",
  });
}

// =====================================
function response(data) {
  return {
    statusCode: 200,
    body: JSON.stringify(data),
  };
                                  }
