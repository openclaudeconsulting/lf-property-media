/* Blocks /CLAUDE.md. A Pages Function's route is its file path minus the .js, and
   Functions win over static assets -- see functions/docs/_middleware.js. */
export const onRequest = () => new Response('Not found', {
  status: 404,
  headers: { 'content-type': 'text/plain; charset=utf-8' },
});
