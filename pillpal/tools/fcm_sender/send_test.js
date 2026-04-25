import admin from 'firebase-admin';

function requiredEnv(name) {
  const v = process.env[name];
  if (!v) throw new Error(`Missing env var: ${name}`);
  return v;
}

// Usage:
// FCM_SERVICE_ACCOUNT_JSON='{"type":"service_account",...}' \
// node send_test.js "<FCM_TOKEN>" "Hello" "Test from script"

const serviceAccountJson = requiredEnv('FCM_SERVICE_ACCOUNT_JSON');
const token = process.argv[2];
const title = process.argv[3] ?? 'Hello from PillPal';
const body = process.argv[4] ?? 'This is a test push notification.';

if (!token) {
  console.error('Usage: node send_test.js "<FCM_TOKEN>" [title] [body]');
  process.exit(1);
}

const serviceAccount = JSON.parse(serviceAccountJson);

if (!admin.apps.length) {
  admin.initializeApp({
    credential: admin.credential.cert(serviceAccount),
  });
}

const message = {
  token,
  notification: { title, body },
  apns: {
    payload: {
      aps: {
        alert: { title, body },
        sound: 'default',
      },
    },
  },
};

const messageId = await admin.messaging().send(message);
console.log('Sent. messageId:', messageId);

