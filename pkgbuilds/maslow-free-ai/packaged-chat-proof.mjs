// Actual unpacked compiled router/dependencies; synthetic keys/fetch only.
import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { mkdtemp, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';
import net from 'node:net';
import { fileURLToPath } from 'node:url';
const packageRoot = path.resolve(process.argv[2]);
const blocker = fileURLToPath(new URL('./test-only-fetch.mjs', import.meta.url));
const directory = await mkdtemp(path.join(tmpdir(), 'maslow-packaged-chat-'));
const socket = net.createServer();
await new Promise(resolve => socket.listen(0, '127.0.0.1', resolve));
const port = socket.address().port;
await new Promise(resolve => socket.close(resolve));
const token = 'synthetic-packaged-chat-token-0000000000000000000000';
const child = spawn(path.join(packageRoot, 'node/bin/node'), ['--import', blocker, path.join(packageRoot, 'router/server/dist/maslow-main.js')], { stdio: ['pipe', 'pipe', 'pipe'] });
let stdout = '', stderr = '';
child.stdout.on('data', bytes => stdout += bytes);
child.stderr.on('data', bytes => stderr += bytes);
const exited = new Promise(resolve => child.once('exit', resolve));
child.stdin.end(JSON.stringify({ encryptionKey: 'a'.repeat(64), instanceToken: token,
  groqKey: 'gsk_synthetic_packaged_chat_0000000000000000', dbPath: path.join(directory, 'router.sqlite'), port }));
try {
  const deadline = Date.now() + 15000;
  while (!stdout.includes('\n') && child.exitCode === null && Date.now() < deadline)
    await new Promise(resolve => setTimeout(resolve, 20));
  assert.equal(JSON.parse(stdout).event, 'ready', 'actual compiled router startup');
  async function request(body) {
    const response = await fetch(`http://127.0.0.1:${port}/v1/chat/completions`, {
      method: 'POST', headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
    const text = await response.text();
    return { status: response.status, body: JSON.parse(text) };
  }
  const messages = [{ role: 'user', content: 'synthetic request' }];
  const text = await request({ model: 'openai/gpt-oss-120b', messages });
  assert.equal(text.status, 200, JSON.stringify(text.body));
  assert.equal(text.body.choices[0].message.content, 'synthetic text response');
  const tools = [{ type: 'function', function: { name: 'sum', parameters: { type: 'object', properties: { a: { type: 'number' }, b: { type: 'number' } }, required: ['a', 'b'] } } }];
  const call = await request({ model: 'openai/gpt-oss-20b', messages, tools });
  assert.equal(call.status, 200, JSON.stringify(call.body));
  const assistant = call.body.choices[0].message;
  assert.equal(assistant.tool_calls[0].function.name, 'sum');
  assert.deepEqual(JSON.parse(assistant.tool_calls[0].function.arguments), { a: 2, b: 3 });
  const result = await request({ model: 'openai/gpt-oss-20b', tools, messages: [...messages, assistant,
    { role: 'tool', tool_call_id: assistant.tool_calls[0].id, content: '5' }] });
  assert.equal(result.status, 200, JSON.stringify(result.body));
  assert.equal(result.body.choices[0].message.content, 'synthetic result 5');
  const media = await request({ model: 'openai/gpt-oss-120b', messages: [{ role: 'user', content: [{ type: 'image_url', image_url: { url: 'https://example.invalid/image' } }] }] });
  assert.equal(media.status, 400, 'media rejected before optional sharp can be used');
  child.kill('SIGTERM');
  await exited;
  assert.equal(child.exitCode, 0);
  assert.equal(stderr, '');
  assert.equal(stdout.split('\n').filter(Boolean).length, 1);
  console.log(JSON.stringify({ actualCompiledRouter: true, packagedDependencyGraph: true, textHttp: true,
    functionCallHttp: true, clientFunctionResultHttp: true, mediaRejected: true,
    syntheticPreloadedFetchOnly: true, realProviderVerified: false }));
} finally {
  if (child.exitCode === null) { child.kill('SIGKILL'); await exited; }
  await rm(directory, { recursive: true, force: true });
}
