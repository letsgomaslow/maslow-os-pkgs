// Test-only preload, never installed. No network request leaves this process.
globalThis.fetch = async (url, init) => {
  if (String(url) !== 'https://api.groq.com/openai/v1/chat/completions')
    throw new Error('Non-Groq network disabled by packaged proof');
  if (init?.method !== 'POST' || init?.redirect !== 'error') throw new Error('Unsafe dispatch');
  const body = JSON.parse(init.body);
  if (!['openai/gpt-oss-120b', 'openai/gpt-oss-20b'].includes(body.model)) throw new Error('Unexpected model');
  const toolResult = body.messages.some(message => message.role === 'tool');
  const message = body.tools?.length && !toolResult
    ? { role: 'assistant', content: null, tool_calls: [{ id: 'call_synthetic', type: 'function', function: { name: 'sum', arguments: '{"a":2,"b":3}' } }] }
    : { role: 'assistant', content: toolResult ? 'synthetic result 5' : 'synthetic text response' };
  return new Response(JSON.stringify({ id: 'synthetic', object: 'chat.completion', created: 1, model: body.model,
    choices: [{ index: 0, message, finish_reason: message.tool_calls ? 'tool_calls' : 'stop' }],
    usage: { prompt_tokens: 2, completion_tokens: 1, total_tokens: 3 } }), { headers: { 'Content-Type': 'application/json' } });
};
