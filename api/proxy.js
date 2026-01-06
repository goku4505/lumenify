export const config = {
  runtime: 'edge',
};

const BACKEND_URL = 'https://chichigoku-lumenify-backend.hf.space';

export default async function handler(request) {
  const url = new URL(request.url);
  
  // Handle CORS preflight
  if (request.method === 'OPTIONS') {
    return new Response(null, {
      status: 200,
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Auth-Token',
        'Access-Control-Max-Age': '86400',
      },
    });
  }
  
  // Extract the path after /api/proxy
  const apiPath = url.pathname.replace(/^\/api\/proxy/, '');
  const targetUrl = `${BACKEND_URL}/api${apiPath}${url.search}`;
  
  console.log(`[PROXY] ${request.method} ${url.pathname} -> ${targetUrl}`);
  
  try {
    // Prepare headers
    const headers = new Headers();
    
    // Forward important headers
    const contentType = request.headers.get('content-type');
    if (contentType) {
      headers.set('Content-Type', contentType);
    }
    
    const authToken = request.headers.get('x-auth-token');
    if (authToken) {
      headers.set('X-Auth-Token', authToken);
    }
    
    const authorization = request.headers.get('authorization');
    if (authorization) {
      headers.set('Authorization', authorization);
    }
    
    // Forward the request to HF backend
    const response = await fetch(targetUrl, {
      method: request.method,
      headers: headers,
      body: request.method !== 'GET' && request.method !== 'HEAD' 
        ? await request.text() 
        : undefined,
    });

    // Get response body
    const responseBody = await response.text();
    
    // Create response with CORS headers
    const responseHeaders = new Headers();
    responseHeaders.set('Access-Control-Allow-Origin', '*');
    responseHeaders.set('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
    responseHeaders.set('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Auth-Token');
    responseHeaders.set('Content-Type', response.headers.get('content-type') || 'application/json');
    
    // Disable buffering for streaming
    responseHeaders.set('X-Accel-Buffering', 'no');
    responseHeaders.set('Cache-Control', 'no-cache');
    
    return new Response(responseBody, {
      status: response.status,
      statusText: response.statusText,
      headers: responseHeaders,
    });
  } catch (error) {
    console.error('[PROXY ERROR]', error);
    return new Response(
      JSON.stringify({ 
        error: 'Proxy error: ' + error.message,
        timestamp: new Date().toISOString()
      }), 
      {
        status: 500,
        headers: {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*',
        },
      }
    );
  }
}
