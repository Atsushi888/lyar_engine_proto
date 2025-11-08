# Floria Chat — Streamlit Edition

フローリアと会話できる、Streamlit 製のシンプルなチャットアプリです。  
**OpenRouter 経由の Meta Llama 3.1 を使用**します（有料・クレジット前払い）。

> **重要**：このアプリは **無料では動きません**。  
> OpenRouter で課金し、APIキー（LLAMA_API_KEY）を設定する必要があります。

---

## 1) Llama（OpenRouter）利用と課金について

- Floria Chat は **OpenRouter** の API を通じて **Meta Llama 3.1** を呼び出します。
- モデル利用は **従量課金（前払いクレジット消費）** です。
- 目安：1 往復の会話で数円〜十数円程度（メッセージ長により変動）。
- 残高が切れると `401` / `403` エラーや無応答になります。

**手順**
1. [OpenRouter](https://openrouter.ai/) にサインアップ  
2. **Billing** でクレジットをチャージ  
3. **API Keys** でキーを発行（`sk-or-...` 形式）

---

## 2) 必要なシークレット（Streamlit Secrets）

Streamlit Cloud の **Secrets** に以下 3 行を貼り付けます（**必ずダブルクォーテーション `"` を含める**）。

```toml
LLAMA_API_KEY = "sk-or-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
LLAMA_BASE_URL = "https://openrouter.ai/api/v1"
LLAMA_MODEL = "meta-llama/llama-3.1-70b-instruct"
```

> **iPad の方へ**：`"` の入力が難しい場合、  
> 上の 3 行を **そのままコピー＆ペースト** して `sk-or-...` の部分だけ自分のキーへ置き換えてください。

---

## 3) はじめかた（Streamlit Cloud）

> このリポジトリは **Streamlit Cloud 前提** の説明のみを提供します。

1. GitHub のこのリポジトリを **Fork**（または自分のアカウントに **Import**）  
2. [streamlit.io](https://streamlit.io) にログイン → **Deploy an app**  
3. 「Repository / Branch / Main file path」を指定  
   - 例:  
     - Repository: `yourname/floria-chat`  
     - Branch: `main`  
     - Main file path: `app.py`（日本語）または `app_multilang.py`（日英切替）
4. デプロイ前に **Advanced settings → Secrets** を開き、下記を貼り付けて **Save**：
   ```toml
   LLAMA_API_KEY = "sk-or-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
   LLAMA_BASE_URL = "https://openrouter.ai/api/v1"
   LLAMA_MODEL = "meta-llama/llama-3.1-70b-instruct"
   ```
5. **Deploy** を実行 → アプリが起動します（自動でブラウザに開く表示は環境により異なります）。

> 注：初回にヒント文が自動表示されないことがあります。空欄のままでもメッセージを送って開始できます。

---

## 4) 使い方のヒント

- 入力欄にメッセージを書いて **送信**。  
- 長文時は **自動継ぎ足し**（Auto-continue）を ON 推奨。  
- **「新しい会話」** は履歴を消します。誤操作防止の確認ダイアログあり（`app.py`/`app_multilang.py` 共通）。

---

## 5) トラブルシューティング

- `401 / 403`：  
  - `LLAMA_API_KEY` 未設定／誤り、または **OpenRouter 残高不足**。  
  - Billing で残高を補充 → Secrets のキーを再確認。
- `429`：レート制限。少し待って再送。  
- `502 / 503`：上流の一時障害。時間を置いて再送。  
- 無応答・途中で途切れる：`max_tokens` が小さすぎる、またはコンテキスト超過。  
- それでもダメ：Secrets の **ダブルクォーテーションが半角か**、曲がった引用符になっていないか確認。

---

## 6) 主なファイル

- `app.py` … 日本語版（リセット確認ダイアログ付き）  
- `app_multilang.py` … 多言語（日英切替）版（リセット確認ダイアログ付き）

---

## 7) ライセンス

MIT License
