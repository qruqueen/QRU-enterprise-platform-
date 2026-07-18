import axios from "axios";

// QRU Online public layer — read-only, no auth token attached.
const BACKEND = process.env.REACT_APP_BACKEND_URL;
export const publicApi = axios.create({ baseURL: `${BACKEND}/api/public` });

export const assetUrl = (u) => {
  if (!u) return null;
  return u.startsWith("http") ? u : `${BACKEND}${u}`;
};
