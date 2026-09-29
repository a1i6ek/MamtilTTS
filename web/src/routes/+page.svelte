<script lang="ts">
	import { tick } from 'svelte';
	import { base64ToBlob, synthesize, VOICES, type SynthesisOptions, type Voice } from '$lib/api';
	import VoiceMessage from '$lib/components/VoiceMessage.svelte';

	type Message =
		| { id: number; from: 'user'; text: string; time: Date }
		| { id: number; from: 'bot'; status: 'pending'; voice: Voice; time: Date }
		| {
				id: number;
				from: 'bot';
				status: 'done';
				voice: Voice;
				blob: Blob;
				duration: number;
				took: number;
				time: Date;
		  }
		| {
				id: number;
				from: 'bot';
				status: 'error';
				voice: Voice;
				error: string;
				retryText: string;
				time: Date;
		  };

	let nextId = 0;
	let messages: Message[] = $state([]);
	let draft = $state('');
	let busy = $state(false);
	let showSettings = $state(false);
	let voice: Voice = $state('man');
	let options: SynthesisOptions = $state({ temperature: 0.667, speaking_rate: 1.0, steps: 10 });

	let list: HTMLElement | undefined = $state();
	let input: HTMLTextAreaElement | undefined = $state();

	const examples = [
		'Саламатсызбы, бул сыноо.',
		'Кыргызстан — тоолуу өлкө.',
		'Бүгүн аба ырайы жакшы.'
	];

	async function scrollToBottom() {
		await tick();
		list?.scrollTo({ top: list.scrollHeight, behavior: 'smooth' });
	}

	const voiceName = (id: Voice) => VOICES.find((v) => v.id === id)?.name ?? id;

	async function send(text = draft, withVoice = voice) {
		text = text.trim();
		if (!text || busy) return;

		draft = '';
		busy = true;
		messages.push({ id: nextId++, from: 'user', text, time: new Date() });
		const botId = nextId++;
		messages.push({
			id: botId,
			from: 'bot',
			status: 'pending',
			voice: withVoice,
			time: new Date()
		});
		scrollToBottom();

		let reply: Message;
		try {
			const result = await synthesize(text, withVoice, $state.snapshot(options));
			reply = {
				id: botId,
				from: 'bot',
				status: 'done',
				voice: withVoice,
				blob: base64ToBlob(result.audio),
				duration: result.duration,
				took: result.processing_time,
				time: new Date()
			};
		} catch (e) {
			const error = e instanceof Error ? e.message : String(e);
			reply = {
				id: botId,
				from: 'bot',
				status: 'error',
				voice: withVoice,
				error: error === 'Failed to fetch' ? 'Cannot reach the TTS server' : error,
				retryText: text,
				time: new Date()
			};
		}

		const index = messages.findIndex((m) => m.id === botId);
		if (index !== -1) messages[index] = reply;
		busy = false;
		scrollToBottom();
		input?.focus();
	}

	function onKeydown(event: KeyboardEvent) {
		if (event.key === 'Enter' && !event.shiftKey && !event.isComposing) {
			event.preventDefault();
			send();
		}
	}

	function autosize(node: HTMLTextAreaElement) {
		$effect(() => {
			void draft;
			node.style.height = 'auto';
			node.style.height = `${Math.min(node.scrollHeight, 160)}px`;
		});
	}

	function formatClock(date: Date) {
		return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
	}
</script>

<svelte:head>
	<title>Mamtil TTS</title>
</svelte:head>

<div class="app">
	<header>
		<div class="avatar" aria-hidden="true">M</div>
		<div class="title">
			<h1>Mamtil TTS</h1>
			<p class:typing={busy}>{busy ? 'recording voice message…' : 'bot'}</p>
		</div>
		<div class="voices" role="radiogroup" aria-label="Voice">
			{#each VOICES as option (option.id)}
				<button
					role="radio"
					aria-checked={voice === option.id}
					class:selected={voice === option.id}
					onclick={() => (voice = option.id)}
				>
					{option.name}
				</button>
			{/each}
		</div>
		<button
			class="icon-btn"
			class:active={showSettings}
			onclick={() => (showSettings = !showSettings)}
			aria-label="Voice settings"
			aria-expanded={showSettings}
		>
			<svg viewBox="0 0 24 24" aria-hidden="true">
				<path d="M4 7h10M18 7h2M4 17h4M12 17h8" />
				<circle cx="16" cy="7" r="2" />
				<circle cx="10" cy="17" r="2" />
			</svg>
		</button>

		{#if showSettings}
			<div class="settings">
				<label>
					<span>Speed <b>{options.speaking_rate.toFixed(2)}</b></span>
					<input type="range" min="0.5" max="2" step="0.05" bind:value={options.speaking_rate} />
					<small>Higher is slower</small>
				</label>
				<label>
					<span>Temperature <b>{options.temperature.toFixed(2)}</b></span>
					<input type="range" min="0" max="1.5" step="0.01" bind:value={options.temperature} />
				</label>
				<label>
					<span>Quality steps <b>{options.steps}</b></span>
					<input type="range" min="1" max="50" step="1" bind:value={options.steps} />
				</label>
			</div>
		{/if}
	</header>

	<main bind:this={list}>
		<div class="messages">
			{#if messages.length === 0}
				<div class="empty">
					<p>Send any text and the bot replies with a voice message.</p>
					<div class="chips">
						{#each examples as example (example)}
							<button onclick={() => send(example)}>{example}</button>
						{/each}
					</div>
				</div>
			{/if}

			{#each messages as message (message.id)}
				<div class="row {message.from}">
					<div class="bubble {message.from}">
						{#if message.from === 'bot'}
							<span class="sender {message.voice}">{voiceName(message.voice)}</span>
						{/if}
						{#if message.from === 'user'}
							<p class="text">{message.text}</p>
							<span class="time">
								{formatClock(message.time)}
								<svg class="check" viewBox="0 0 18 12" aria-hidden="true">
									<path d="M1 6.5 4.5 10 11 2M7 10l1 0L15 2" />
								</svg>
							</span>
						{:else if message.status === 'pending'}
							<div class="pending" aria-label="Generating audio">
								<span></span><span></span><span></span>
							</div>
						{:else if message.status === 'done'}
							<VoiceMessage blob={message.blob} duration={message.duration} autoplay />
							<span class="time">{message.took.toFixed(2)}s · {formatClock(message.time)}</span>
						{:else}
							<p class="error">{message.error}</p>
							<button
								class="retry"
								onclick={() => send(message.retryText, message.voice)}
								disabled={busy}>Retry</button
							>
							<span class="time">{formatClock(message.time)}</span>
						{/if}
					</div>
				</div>
			{/each}
		</div>
	</main>

	<footer>
		<form
			onsubmit={(e) => {
				e.preventDefault();
				send();
			}}
		>
			<textarea
				bind:this={input}
				bind:value={draft}
				{@attach autosize}
				onkeydown={onKeydown}
				placeholder="Message"
				rows="1"
				maxlength="1000"></textarea>
			<button type="submit" class="send" disabled={!draft.trim() || busy} aria-label="Send">
				<svg viewBox="0 0 24 24" aria-hidden="true">
					<path d="M3.4 20.4 21 12 3.4 3.6l-.01 6.53L15 12 3.39 13.87z" />
				</svg>
			</button>
		</form>
	</footer>
</div>

<style>
	:global(:root) {
		--bg: #8eb488;
		--pattern: rgba(255, 255, 255, 0.12);
		--panel: #ffffff;
		--bubble-in: #ffffff;
		--bubble-out: #effdde;
		--text: #0f1419;
		--text-muted: #707579;
		--time-out: #5fad63;
		--accent: #3390ec;
		--woman: #c03d96;
		--wave-idle: #c7d6e4;
		--border: #e4e4e4;
		--input-bg: #ffffff;
		--error: #e53935;
		--shadow: 0 1px 2px rgba(16, 35, 47, 0.15);
	}

	@media (prefers-color-scheme: dark) {
		:global(:root) {
			--bg: #0e1621;
			--pattern: rgba(255, 255, 255, 0.025);
			--panel: #17212b;
			--bubble-in: #182533;
			--bubble-out: #2b5278;
			--text: #f5f5f5;
			--text-muted: #7d8b99;
			--time-out: #7da8d3;
			--accent: #5eb5f7;
			--woman: #f07cc4;
			--wave-idle: #3a4d60;
			--border: #0e1621;
			--input-bg: #17212b;
			--error: #ff6b6b;
			--shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
		}
	}

	:global(html, body) {
		margin: 0;
		height: 100%;
		background: var(--bg);
		color: var(--text);
		font-family:
			-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
		-webkit-font-smoothing: antialiased;
	}

	:global(*) {
		box-sizing: border-box;
	}

	.app {
		display: flex;
		flex-direction: column;
		height: 100dvh;
		max-width: 760px;
		margin: 0 auto;
		background-color: var(--bg);
		background-image: radial-gradient(var(--pattern) 1.5px, transparent 1.5px);
		background-size: 22px 22px;
	}

	header {
		position: relative;
		display: flex;
		align-items: center;
		gap: 12px;
		padding: 8px 16px;
		background: var(--panel);
		border-bottom: 1px solid var(--border);
		z-index: 2;
	}

	.avatar {
		width: 42px;
		height: 42px;
		border-radius: 50%;
		display: grid;
		place-items: center;
		font-weight: 600;
		font-size: 18px;
		color: #fff;
		background: linear-gradient(135deg, #72d5fd, #2a9ef1);
	}

	.title {
		flex: 1;
		min-width: 0;
	}

	h1 {
		margin: 0;
		font-size: 16px;
		font-weight: 600;
	}

	.title p {
		margin: 1px 0 0;
		font-size: 13px;
		color: var(--text-muted);
	}

	.title p.typing {
		color: var(--accent);
	}

	.voices {
		display: flex;
		padding: 3px;
		border-radius: 18px;
		background: color-mix(in srgb, var(--text-muted) 14%, transparent);
	}

	.voices button {
		padding: 6px 14px;
		border: none;
		border-radius: 15px;
		background: none;
		color: var(--text-muted);
		font: inherit;
		font-size: 14px;
		font-weight: 500;
		cursor: pointer;
		transition:
			background 0.15s,
			color 0.15s;
	}

	.voices button.selected {
		background: var(--accent);
		color: #fff;
	}

	.sender {
		display: block;
		margin-bottom: 4px;
		font-size: 14px;
		font-weight: 600;
		color: var(--accent);
	}

	.sender.woman {
		color: var(--woman);
	}

	.icon-btn {
		width: 40px;
		height: 40px;
		border: none;
		border-radius: 50%;
		background: none;
		color: var(--text-muted);
		display: grid;
		place-items: center;
		cursor: pointer;
	}

	.icon-btn:hover,
	.icon-btn.active {
		background: color-mix(in srgb, var(--text-muted) 12%, transparent);
		color: var(--accent);
	}

	.icon-btn svg {
		width: 22px;
		height: 22px;
		fill: none;
		stroke: currentColor;
		stroke-width: 2;
		stroke-linecap: round;
	}

	.settings {
		position: absolute;
		top: calc(100% + 6px);
		right: 12px;
		width: min(300px, calc(100vw - 24px));
		padding: 14px 16px;
		display: grid;
		gap: 14px;
		background: var(--panel);
		border-radius: 12px;
		box-shadow: 0 6px 24px rgba(0, 0, 0, 0.2);
	}

	.settings label {
		display: grid;
		gap: 6px;
		font-size: 14px;
	}

	.settings span {
		display: flex;
		justify-content: space-between;
	}

	.settings b {
		color: var(--accent);
		font-weight: 600;
		font-variant-numeric: tabular-nums;
	}

	.settings small {
		color: var(--text-muted);
		font-size: 12px;
		margin-top: -4px;
	}

	.settings input {
		width: 100%;
		accent-color: var(--accent);
	}

	main {
		flex: 1;
		overflow-y: auto;
		padding: 12px 12px 4px;
	}

	.messages {
		display: flex;
		flex-direction: column;
		gap: 6px;
		min-height: 100%;
		justify-content: flex-end;
	}

	.empty {
		margin: auto;
		max-width: 320px;
		padding: 16px;
		text-align: center;
		border-radius: 16px;
		background: rgba(0, 0, 0, 0.18);
		color: #fff;
		font-size: 14px;
	}

	.empty p {
		margin: 0 0 12px;
	}

	.chips {
		display: grid;
		gap: 6px;
	}

	.chips button {
		padding: 8px 12px;
		border: none;
		border-radius: 12px;
		background: rgba(255, 255, 255, 0.2);
		color: #fff;
		font: inherit;
		cursor: pointer;
	}

	.chips button:hover {
		background: rgba(255, 255, 255, 0.3);
	}

	.row {
		display: flex;
		animation: pop 0.18s ease-out;
	}

	.row.user {
		justify-content: flex-end;
	}

	.bubble {
		position: relative;
		max-width: min(480px, 85%);
		padding: 6px 10px 6px;
		border-radius: 16px;
		box-shadow: var(--shadow);
		overflow-wrap: anywhere;
	}

	.bubble.user {
		background: var(--bubble-out);
		border-bottom-right-radius: 4px;
	}

	.bubble.bot {
		background: var(--bubble-in);
		border-bottom-left-radius: 4px;
	}

	.text {
		display: inline;
		margin: 0;
		font-size: 15px;
		line-height: 1.35;
		white-space: pre-wrap;
	}

	.time {
		float: right;
		display: inline-flex;
		align-items: center;
		gap: 3px;
		margin: 6px 0 -2px 10px;
		font-size: 12px;
		color: var(--text-muted);
		white-space: nowrap;
	}

	.bubble.user .time {
		color: var(--time-out);
	}

	.check {
		width: 16px;
		height: 11px;
		fill: none;
		stroke: currentColor;
		stroke-width: 1.6;
		stroke-linecap: round;
		stroke-linejoin: round;
	}

	.pending {
		display: flex;
		gap: 4px;
		padding: 10px 6px;
	}

	.pending span {
		width: 8px;
		height: 8px;
		border-radius: 50%;
		background: var(--accent);
		animation: bounce 1.2s infinite ease-in-out;
	}

	.pending span:nth-child(2) {
		animation-delay: 0.15s;
	}

	.pending span:nth-child(3) {
		animation-delay: 0.3s;
	}

	.error {
		margin: 2px 0 6px;
		font-size: 14px;
		color: var(--error);
	}

	.retry {
		padding: 4px 12px;
		border: 1px solid var(--accent);
		border-radius: 12px;
		background: none;
		color: var(--accent);
		font: inherit;
		font-size: 13px;
		cursor: pointer;
	}

	.retry:disabled {
		opacity: 0.5;
		cursor: default;
	}

	footer {
		padding: 8px 12px calc(12px + env(safe-area-inset-bottom));
	}

	form {
		display: flex;
		align-items: flex-end;
		gap: 8px;
	}

	textarea {
		flex: 1;
		resize: none;
		padding: 12px 16px;
		border: none;
		border-radius: 22px;
		background: var(--input-bg);
		color: var(--text);
		font: inherit;
		font-size: 15px;
		line-height: 1.35;
		box-shadow: var(--shadow);
		outline: none;
	}

	textarea::placeholder {
		color: var(--text-muted);
	}

	.send {
		flex: none;
		width: 46px;
		height: 46px;
		border: none;
		border-radius: 50%;
		background: var(--accent);
		color: #fff;
		display: grid;
		place-items: center;
		cursor: pointer;
		box-shadow: var(--shadow);
		transition:
			transform 0.1s,
			opacity 0.15s;
	}

	.send:disabled {
		opacity: 0.55;
		cursor: default;
	}

	.send:not(:disabled):active {
		transform: scale(0.94);
	}

	.send svg {
		width: 22px;
		height: 22px;
		fill: currentColor;
	}

	@keyframes pop {
		from {
			opacity: 0;
			transform: translateY(6px) scale(0.98);
		}
	}

	@keyframes bounce {
		0%,
		80%,
		100% {
			transform: scale(0.6);
			opacity: 0.5;
		}
		40% {
			transform: scale(1);
			opacity: 1;
		}
	}
</style>
