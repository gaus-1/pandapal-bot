# Changelog

All notable changes to PandaPal will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- GitHub community files (CONTRIBUTING, CODE_OF_CONDUCT, SECURITY)
- Comprehensive documentation structure
- Pull request template

## [2.0.0] - 2026-01-23

### Added
- Enhanced RAG system with multi-query expansion and reranking
- Semantic caching for similar queries (75-90% token savings)
- Context compression for efficient token usage
- Homework checking via photo with detailed error analysis
- Adaptive learning system tracking problem topics
- Adult topics explanation service for life questions
- Comprehensive E2E tests covering all features
- Streaming responses via Server-Sent Events
- YandexART image generation support

### Changed
- Upgraded to YandexGPT Pro for all users
- Improved AI prompts for structured responses
- Modular AI chat structure (split 1406-line file into modules)
- Temperature increased to 0.7 for more natural responses
- Enhanced visualization generation with 4-paragraph explanations

### Fixed
- Duplicate achievement unlocks
- King promotion bug in Checkers
- Erudite score calculation for all words
- AI move logic for Checkers (now uses get_valid_moves)
- Frontend authentication flow (extract user from response)
- Erudite tile display before move confirmation

### Security
- Added validation for dark cells only in Checkers
- Improved piece ownership checks
- Enhanced content moderation (150+ patterns)

## [1.5.0] - 2025-12-15

### Added
- YooKassa production mode with saved cards
- Premium subscriptions (Month 399₽, Year 2990₽)
- Auto-renewal for subscriptions
- Games: Erudite (Scrabble), Checkers improvements
- Dark theme for all screens
- Welcome screen with logo animation

### Changed
- Migrated from Telegram Stars to YooKassa
- Improved payment webhook handling
- Enhanced UI/UX with pastel colors

### Fixed
- Audio conversion (WebM to OGG)
- Payment method unlinking
- Daily request limits tracking

## [1.0.0] - 2025-10-01

### Added
- Initial release
- Telegram bot with AI chat
- Mini App with React frontend
- Basic games (TicTacToe, 2048)
- Achievement system
- Basic moderation

[Unreleased]: https://github.com/gaus-1/pandapal-bot/compare/v2.0.0...HEAD
[2.0.0]: https://github.com/gaus-1/pandapal-bot/compare/v1.5.0...v2.0.0
[1.5.0]: https://github.com/gaus-1/pandapal-bot/compare/v1.0.0...v1.5.0
[1.0.0]: https://github.com/gaus-1/pandapal-bot/releases/tag/v1.0.0
