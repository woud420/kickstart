{
  "name": "{{ package_name }}",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "packageManager": "bun@{{ bun_version }}",
  "scripts": {
    "build": "make worker-build-release",
    "dev": "wrangler dev",
    "deploy": "wrangler deploy"
  },
  "devDependencies": {
    "wrangler": "^4.80.0"
  }
}
