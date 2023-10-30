export function getIdFromFullAccessPath(fullAccessPath: string) {
  // Replace '].' with a single dash
  let id = fullAccessPath.replace(/\]\./g, '-');

  // Replace any character that is not a word character or underscore with a dash
  id = id.replace(/[^\w_]+/g, '-');

  // Remove any trailing dashes
  id = id.replace(/-+$/, '');

  return id;
}
