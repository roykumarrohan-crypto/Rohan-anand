import test from 'node:test';
import assert from 'node:assert/strict';
import {
  checkRoleHierarchy,
  parseDurationToSeconds,
  matchAutoresponder,
  calculatePollTally,
  isAntiNukeThresholdBreached,
  UserMember,
  AutoresponderRule,
  AntiNukeAction
} from './simulatorEngine';

test('checkRoleHierarchy prevents self moderation', () => {
  const mod: UserMember = { id: 'user-1', name: 'ModAlex', role: 'moderator', roleHierarchy: 50 };
  const err = checkRoleHierarchy(mod, mod);
  assert.equal(err, 'You cannot moderate yourself.');
});

test('checkRoleHierarchy prevents moderating bot itself', () => {
  const mod: UserMember = { id: 'user-1', name: 'ModAlex', role: 'moderator', roleHierarchy: 50 };
  const bot: UserMember = { id: 'cosmic-bot', name: 'Cosmic ki baddie', role: 'admin', roleHierarchy: 90 };
  const err = checkRoleHierarchy(mod, bot, 'cosmic-bot');
  assert.equal(err, 'Cosmic ki baddie cannot moderate herself! ✨');
});

test('checkRoleHierarchy prevents targeting higher or equal role', () => {
  const mod: UserMember = { id: 'mod-1', name: 'JuniorMod', role: 'moderator', roleHierarchy: 50 };
  const admin: UserMember = { id: 'admin-1', name: 'SeniorAdmin', role: 'admin', roleHierarchy: 80 };
  const err = checkRoleHierarchy(mod, admin);
  assert.match(err || '', /their role hierarchy \(80\) is equal to or higher than yours/);
});

test('checkRoleHierarchy permits owner to moderate anyone except self', () => {
  const owner: UserMember = { id: 'owner-1', name: 'ServerOwner', role: 'owner', roleHierarchy: 100 };
  const admin: UserMember = { id: 'admin-1', name: 'SeniorAdmin', role: 'admin', roleHierarchy: 80 };
  const err = checkRoleHierarchy(owner, admin);
  assert.equal(err, null);
});

test('parseDurationToSeconds parses standard time strings', () => {
  assert.equal(parseDurationToSeconds('10s'), 10);
  assert.equal(parseDurationToSeconds('30m'), 1800);
  assert.equal(parseDurationToSeconds('2h'), 7200);
  assert.equal(parseDurationToSeconds('1d'), 86400);
  assert.equal(parseDurationToSeconds('invalid'), null);
});

test('matchAutoresponder checks exact, contains, startswith', () => {
  const ruleExact: AutoresponderRule = {
    id: 1,
    trigger: 'hello',
    response: 'Welcome!',
    matchType: 'exact',
    isEmbed: false,
    isEnabled: true,
    cooldownSec: 5
  };

  assert.equal(matchAutoresponder('Hello', ruleExact), true);
  assert.equal(matchAutoresponder('hello world', ruleExact), false);

  const ruleContains: AutoresponderRule = {
    id: 2,
    trigger: 'rules',
    response: 'See #rules',
    matchType: 'contains',
    isEmbed: true,
    isEnabled: true,
    cooldownSec: 5
  };
  assert.equal(matchAutoresponder('Where are the rules please?', ruleContains), true);
  assert.equal(matchAutoresponder('Hello general', ruleContains), false);

  const ruleStart: AutoresponderRule = {
    id: 3,
    trigger: 'quest',
    response: 'Quest started!',
    matchType: 'startswith',
    isEmbed: false,
    isEnabled: true,
    cooldownSec: 5
  };
  assert.equal(matchAutoresponder('quest accept 10', ruleStart), true);
  assert.equal(matchAutoresponder('my quest', ruleStart), false);
});

test('calculatePollTally computes count, percentage and ascii bar', () => {
  const votes = { 0: 3, 1: 1 };
  const tally = calculatePollTally(votes, 0, 4, 10);
  assert.equal(tally.count, 3);
  assert.equal(tally.percentage, 75);
  assert.equal(tally.progressBar, '████████░░');
});

test('isAntiNukeThresholdBreached flags rapid destructive actions', () => {
  const now = 1000;
  const actions: AntiNukeAction[] = [
    { userId: 'spammer-1', actionType: 'channel_delete', timestamp: 980 },
    { userId: 'spammer-1', actionType: 'channel_delete', timestamp: 985 },
    { userId: 'spammer-1', actionType: 'channel_delete', timestamp: 990 },
  ];

  // Threshold is 3 within 60s
  const breached = isAntiNukeThresholdBreached(actions, 'spammer-1', 'channel_delete', 3, 60, now);
  assert.equal(breached, true);

  // Spammer 2 has only 1 action
  const safe = isAntiNukeThresholdBreached(actions, 'user-safe', 'channel_delete', 3, 60, now);
  assert.equal(safe, false);
});
