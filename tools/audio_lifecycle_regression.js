"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const bridge = fs.readFileSync("godot/web/audio_bridge.js", "utf8");
const game = fs.readFileSync("godot/scripts/story/story_game.gd", "utf8");

// Same canonical browser lifecycle mock suite; presentation is now extracted.
assert.match(game, /AudioServer\.set_bus_mute/);
assert.match(game, /else:\s*\n\s*music = AudioStreamPlayer.new/);
assert.match(game, /if music != null and not music.playing: music.play/);
assert.match(bridge, /if \(window.VorGunAudio\?\.isWebAudioOwner\) return/);
assert.match(bridge, /open: "door_open_office.wav"/);
assert.match(bridge, /flush: "tube_water_flush.wav"/);
assert.match(bridge, /kind === "flush" \? play\("flush"\)/);

async function flush() {
  for (let i = 0; i < 8; i++) await Promise.resolve();
}
async function browserCase(deviceName, userAgent, pendingFirstPlay) {
  const listeners = new Map();
  const events = [];
  const audioObjects = [];
  const state = { startedBuffers: 0, firstPlayResolve: null, rejectNextPlay: false, resumes: 0 };
  const document = {
    baseURI: "https://example.test/VorGun/",
    hidden: false,
    addEventListener(name, fn) {
      if (!listeners.has(name)) listeners.set(name, []);
      listeners.get(name).push(fn);
    }
  };
  class FakeAudio {
    constructor(url) {
      this.src = url;
      this.paused = true;
      this.volume = 1;
      this.playCalls = 0;
      this.currentTime = 0;
      audioObjects.push(this);
    }
    play() {
      this.playCalls++;
      events.push("play");
      if (state.rejectNextPlay) {
        state.rejectNextPlay = false;
        return Promise.reject(new Error("NotAllowedError"));
      }
      if (pendingFirstPlay && this.playCalls === 1) {
        return new Promise(resolve => {
          state.firstPlayResolve = () => { this.paused = false; resolve(); };
        });
      }
      this.paused = false;
      return Promise.resolve();
    }
    pause() { this.paused = true; events.push("pause"); }
  }
  class FakeAudioContext {
    constructor() { this.state = "running"; this.currentTime = 0; this.destination = {}; state.context = this; }
    resume() { state.resumes++; this.state = "running"; return Promise.resolve(); }
    createGain() { const gain = { gain: { value: 1, setValueAtTime() {}, exponentialRampToValueAtTime() {} }, connect() {} }; state.gainNodes = state.gainNodes || []; state.gainNodes.push(gain); return gain; }
    createMediaElementSource() { state.mediaSources = (state.mediaSources || 0) + 1; return { connect() {} }; }
    decodeAudioData() { return Promise.resolve({ length: 2200 }); }
    createOscillator() { return { frequency: { setValueAtTime() {}, exponentialRampToValueAtTime() {} }, connect() {}, start() {}, stop() {} }; }
    createBufferSource() {
      return { buffer: null, connect() {}, start() { state.startedBuffers++; } };
    }
  }
  const window = { AudioContext: FakeAudioContext };
  const sandbox = {
    window, document, navigator: { userAgent, platform: "iPhone", maxTouchPoints: 5 },
    Audio: FakeAudio, URL, Promise,
    fetch: () => Promise.resolve({ ok: true, arrayBuffer: () => Promise.resolve(new ArrayBuffer(16)) }),
    console: { warn() {}, debug() {} }
  };
  vm.runInNewContext(bridge, sandbox, { filename: "audio_bridge.js" });
  const audio = window.VorGunAudio;
  assert.equal(audio.isWebAudioOwner, true, deviceName + " must be browser-owned");
  assert.equal(audioObjects.length, 1, "Only one background music Audio element is created");

  // Music ON on first screen. Touch is a real user gesture.
  listeners.get("click")[0]({ isTrusted: true });
  audio.startMusic(); // Selecting Cooper, no duplicate
  audio.startMusic(); // Entering Operations, no duplicate
  audio.startMusic(); // Returning to map, no duplicate
  assert.equal(audioObjects[0].playCalls, 1,
    deviceName + " must have exactly one play request across scene changes");
  if (state.firstPlayResolve) state.firstPlayResolve();
  await flush();
  assert.equal(audio.diagnostic().musicStarts, 1,
    "Only one active music playback after all transitions");
  audio.startMusic();
  await flush();
  assert.equal(audioObjects[0].playCalls, 1, "Repeated calls do not rewind or layer music");

  // Game Menu: volume and SFX are independent.
  audio.setVolume(0.31);
  assert.equal(audioObjects[0].volume, 1, "iOS WebAudio owns gain; element volume remains 1");
  assert.equal(state.mediaSources, 1, "Exactly one music MediaElementAudioSource");
  assert.equal(state.gainNodes[1].gain.value, 0.31, "Music volume controls dedicated WebAudio gain, not SFX");
  audio.setSfxVolume(0.27);
  await flush();
  audio.playHop();
  audio.playDoor(true);
  audio.playDoor(false);
  audio.playAction("menu");
  audio.playAction("select");
  const musicRequestsBeforeFlush = audioObjects[0].playCalls;
  audio.playAction("flush");
  audio.playAction("birds");
  audio.playAction("boat");
  assert.equal(audioObjects[0].playCalls, musicRequestsBeforeFlush,
    "Tube suction SFX must never restart background music");
  assert.ok(state.startedBuffers >= 5, deviceName + " must play short SFX through WebAudio");

  audio.setMusicEnabled(false);
  assert.equal(audioObjects[0].paused, true);
  audio.playHop();
  assert.ok(state.startedBuffers >= 6, "Muting music must not mute SFX");
  audio.setSfxEnabled(false);
  const before = state.startedBuffers;
  audio.playHop();
  assert.equal(state.startedBuffers, before, "Muting SFX must prevent SFX playback");
  audio.setSfxEnabled(true);
  audio.setMusicEnabled(true);
  await flush();
  assert.equal(audioObjects[0].playCalls, 2, "Music ON must resume existing player once");
  audio.startMusic();
  assert.equal(audioObjects[0].playCalls, 2, "Scene change after resume cannot start another stream");
  assert.equal(audioObjects.length, 1, "Still only one HTML music element after resume");

  vm.runInNewContext(bridge, sandbox, { filename: "audio_bridge.js [repeat]" });
  assert.equal(audioObjects.length, 1, "Duplicate script injection must not construct another audio player");
  assert.equal(listeners.get("click").length, 1, "Duplicate injection cannot add an unlock handler");

  // iPhone returns from background with suspended WebAudio while music is
  // flagged as enabled: the next touch must wake the existing audio graph.
  state.context.state = "suspended";
  const playCountBeforeResume = audioObjects[0].playCalls;
  listeners.get("touchend")[0]({ isTrusted: true });
  await flush();
  assert.equal(state.context.state, "running", "Returning to iPhone must resume suspended WebAudio");
  assert.equal(audioObjects[0].playCalls, playCountBeforeResume,
    "Resuming an active track cannot start overlapping music");

  // First retry can be rejected by mobile autoplay policy; following trusted
  // gesture must retry without a reload, toggling music, or spawning players.
  state.rejectNextPlay = true;
  audioObjects[0].pause();
  listeners.get("click")[0]({ isTrusted: true });
  await flush();
  assert.equal(audioObjects[0].paused, true, "Rejected autoplay leaves music paused");
  listeners.get("click")[0]({ isTrusted: true });
  await flush();
  assert.equal(audioObjects[0].paused, false, "Next tap must recover from rejected mobile music.play()");
  assert.equal(audioObjects[0].playCalls, playCountBeforeResume + 2,
    "Recovery must have exactly one rejected request and one successful retry");

  // Switching back from another app also tries to restart the existing owner.
  document.hidden = true;
  listeners.get("visibilitychange")[0]();
  audioObjects[0].pause();
  state.context.state = "suspended";
  document.hidden = false;
  listeners.get("visibilitychange")[0]();
  await flush();
  assert.equal(state.context.state, "running", "Visibility restore must resume music context");
  assert.equal(audioObjects[0].paused, false, "Visibility restore should attempt paused music");
  assert.equal(audioObjects.length, 1, "Music recovery cannot create duplicate music owners");
  process.stdout.write("PASS " + deviceName + " — music resume, trusted-touch retry, independent SFX\n");
}
(async () => {
  await browserCase("iPhone Chrome", "Mozilla/5.0 (iPhone; CPU iPhone OS 18_6 like Mac OS X) CriOS/128", true);
  await browserCase("Desktop Chrome Web", "Mozilla/5.0 (X11; Linux x86_64) Chrome/128.0", false);
})().catch(error => { console.error(error); process.exitCode = 1; });
