// Command tab entry — the v7.1 Command center is split into focused
// components under ./command/ (see ./command/CommandCenter.jsx for the
// container and the v7.1 correction notes). This shim keeps the existing
// import path stable (App.jsx lazy-imports ./components/CommandCenter).

import { CommandCenter } from './command/CommandCenter';

export { CommandCenter };
export default CommandCenter;
