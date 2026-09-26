// Every time on these pages is shown on the viewer's own clock, and only the browser
// knows which zone that is. Rendering on the server would print times in the server's
// zone first and then jump when the page hydrates, so the dashboard renders in the
// browser. Data still loads on the server (+layout.server.ts / +page.server.ts).
export const ssr = false;
