const { exec } = require("child_process");

exports.handler = async (event) => {
  const url = event.queryStringParameters?.url;

  if (!url) {
    return {
      statusCode: 400,
      body: JSON.stringify({ error: "URL required" }),
    };
  }

  return new Promise((resolve) => {
    exec(`python3 netlify/functions/script.py "${url}"`, (error, stdout, stderr) => {
      if (error) {
        resolve({
          statusCode: 500,
          body: stderr,
        });
        return;
      }

      resolve({
        statusCode: 200,
        body: stdout,
      });
    });
  });
};
