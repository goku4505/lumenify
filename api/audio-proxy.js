export const config = {
  runtime: 'edge',
};

const BACKEND_URL = 'https://chichigoku-lumenify-backend.hf.space';

export default async function handler(request) {
  const url = new URL(request.url);
  
  if (request.method === 'OPTIONS') {
    return new Response(null, {
      status: 200,
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, HEAD, OPTIONS',
        'Access-Control-Allow-Headers': 'Range, Content-Type',
        'Access-Control-Max-Age': '86400',
      },
    });
  }
  
  const audioPath = url.pathname.replace(/^\/api\/audio-proxy/, '');
  const targetUrl = `${BACKEND_URL}/audio${audioPath}`;
  
  console.log(`[AUDIO PROXY] ${request.method} ${url.pathname} -> ${targetUrl}`);
  
  try {
    const headers = new Headers();
    
    const rangeHeader = request.headers.get('range');
    if (rangeHeader) {
      headers.set('Range', rangeHeader);
    }
    
    const response = await fetch(targetUrl, { 
      method: request.method,
      headers: headers 
    });

    if (!response.ok) {
      console.error(`[AUDIO ERROR] ${response.status} ${response.statusText}`);
      throw new Error(`Audio not found: ${response.status}`);
    }

    const responseHeaders = new Headers(response.headers);
    
    responseHeaders.set('Access-Control-Allow-Origin', '*');
    responseHeaders.set('Access-Control-Expose-Headers', 'Content-Range, Content-Length, Accept-Ranges');
    
    responseHeaders.set('Cache-Control', 'public, max-age=3600');
    
    if (!responseHeaders.has('content-type')) {
      responseHeaders.set('Content-Type', 'audio/mpeg');
    }
    
    responseHeaders.set('X-Accel-Buffering', 'no');
    
    return new Response(response.body, {
      status: response.status,
      statusText: response.statusText,
      headers: responseHeaders,
    });
  } catch (error) {
    console.error('[AUDIO PROXY ERROR]', error);
    return new Response(
      JSON.stringify({ 
        error: 'Audio file not found',
        path: audioPath,
        timestamp: new Date().toISOString()
      }), 
      {
        status: 404,
        headers: { 
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*',
        },
      }
    );
  }
}
