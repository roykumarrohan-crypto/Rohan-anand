/**
 * Pure logic engine powering the Cosmic ki baddie Discord simulator and bot routines.
 */

export interface GuildConfig {
  guildId: string;
  prefix: string;
  welcomeChannelId: string;
  modLogChannelId: string;
  ticketCategoryId: string;
  ticketSupportRoleId: string;
  antiNukeEnabled: boolean;
  protectionMode: 'SAFE_MODE' | 'SERVER_PROTECTION' | 'EMERGENCY_LOCKDOWN';
  maxWarnings: number;
}

export interface UserMember {
  id: string;
  name: string;
  avatar: string;
  role: 'owner' | 'admin' | 'moderator' | 'helper' | 'member';
  roleHierarchy: number; // Higher number = higher priority
}

export interface AutoresponderRule {
  id: number;
  trigger: string;
  response: string;
  matchType: 'exact' | 'contains' | 'startswith';
  isEmbed: boolean;
  isEnabled: boolean;
  cooldownSec: number;
}

export interface AntiNukeAction {
  userId: string;
  actionType: string;
  timestamp: number;
}

/**
 * Checks role hierarchy safety between moderator and target.
 * Returns null if allowed, or error message string if prohibited.
 */
export function checkRoleHierarchy(
  moderator: UserMember,
  target: UserMember,
  botUserId: string = 'cosmic-bot'
): string | null {
  if (moderator.id === target.id) {
    return 'You cannot moderate yourself.';
  }
  if (target.id === botUserId) {
    return 'Cosmic ki baddie cannot moderate herself! ✨';
  }
  if (target.role === 'owner') {
    return 'You cannot moderate the server owner.';
  }
  if (moderator.role !== 'owner' && target.roleHierarchy >= moderator.roleHierarchy) {
    return `Cannot target ${target.name}: their role hierarchy (${target.roleHierarchy}) is equal to or higher than yours (${moderator.roleHierarchy}).`;
  }
  return null;
}

/**
 * Parses duration strings like 10s, 30m, 2h, 1d into total seconds.
 */
export function parseDurationToSeconds(durationStr: string): number | null {
  const match = durationStr.trim().toLowerCase().match(/^(\d+)([smhd])$/);
  if (!match) return null;
  const val = parseInt(match[1], 10);
  const unit = match[2];
  const multipliers: Record<string, number> = {
    s: 1,
    m: 60,
    h: 3600,
    d: 86400,
  };
  return val * (multipliers[unit] || 0);
}

/**
 * Checks whether an incoming message content triggers an autoresponder rule.
 */
export function matchAutoresponder(
  messageContent: string,
  rule: AutoresponderRule
): boolean {
  if (!rule.isEnabled) return false;
  const content = messageContent.trim().toLowerCase();
  const trigger = rule.trigger.trim().toLowerCase();

  if (rule.matchType === 'exact') {
    return content === trigger;
  }
  if (rule.matchType === 'contains') {
    return content.includes(trigger);
  }
  if (rule.matchType === 'startswith') {
    return content.startsWith(trigger);
  }
  return false;
}

/**
 * Calculates poll vote tallies and generates ascii progress bar.
 */
export function calculatePollTally(
  votes: Record<number, number>,
  optionIndex: number,
  totalVotes: number,
  barLength: number = 10
): { count: number; percentage: number; progressBar: string } {
  const count = votes[optionIndex] || 0;
  const percentage = totalVotes > 0 ? (count / totalVotes) * 100 : 0;
  const filled = Math.min(barLength, Math.max(0, Math.round((barLength * percentage) / 100)));
  const empty = barLength - filled;
  const progressBar = '█'.repeat(filled) + '░'.repeat(empty);

  return { count, percentage, progressBar };
}

/**
 * Anti-nuke rate limit checker. Returns true if user breached threshold within window.
 */
export function isAntiNukeThresholdBreached(
  actions: AntiNukeAction[],
  userId: string,
  actionType: string,
  threshold: number,
  windowSeconds: number,
  currentTimeSec: number
): boolean {
  const cutoff = currentTimeSec - windowSeconds;
  const matchingActions = actions.filter(
    (a) => a.userId === userId && a.actionType === actionType && a.timestamp >= cutoff
  );
  return matchingActions.length >= threshold;
}
