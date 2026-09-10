# Malloc's Vroid Blender Tools

Blender 5.0 以降向けの、シンプルな VRoid 整理ツールです。

[English](README.md)

**VRoid Studio から書き出した `.vrm` ファイル**を対象としています。
VRoid Studio のプロジェクトファイル（`.vroid`）を開いたり編集したりする機能はありません。

- **Bones:** VRoid のボーン名を整理し、左右に Blender 形式の `.L` / `.R` を付けます。
- **Mesh:** 選択したメッシュをマテリアルごとに分離します。
- **Convert:** MToon の基本的な入力を Principled BSDF に転送します。
- **Rename:** `N00_000_00_FaceMouth_00_FACE (Instance)` → `FaceMouth` のようにマテリアル名を整理します。
  また、マテリアル名を使ってオブジェクトとメッシュデータの名前を変更できます。

各機能は個別に実行できます。
マテリアルの変換、マテリアル名の変更、オブジェクト名の変更は独立しています。

## 動作要件

- Blender 5.0 以降。
- 使用する Blender に対応した公式の [VRM Add-on for Blender](https://vrm-addon-for-blender.info/en-us/) をインストールし、有効にしてください。
- 上記アドオンで VRM 0.x または VRM 1.0 として読み込んだ VRoid モデル。

メッシュの分離とオブジェクト／メッシュ名の変更は、通常の Blender メッシュにも使えます。
この 2 つの機能には、VRM メタデータや VRM Add-on は不要です。

## インストール

1. [GitHub リリースの Assets](https://github.com/kanzaki1201/malloc-vroid-blender-tools/releases/latest) から `vroid_blender_tools-0.3.0.zip` をダウンロードします。
2. Blender で **編集 → プリファレンス → エクステンションを入手**（**Edit → Preferences → Get Extensions**）を開きます。
3. 右上のメニューから **ディスクからインストール**（**Install from Disk**）を選びます。
4. ダウンロードした ZIP を選び、**Malloc's Vroid Blender Tools** を有効にします。

インストールには、ビルド済みのエクステンション ZIP を使ってください。
GitHub のソースコード ZIP や `__init__.py` は選ばないでください。

## 基本的な使い方

変更前にモデルのコピーを保存してください。

1. VRoid Studio から `.vrm` を書き出し、公式の VRM Add-on で読み込みます。
   ボーン・マテリアルの操作ではアーマチュアを、メッシュの操作ではメッシュを選択します。
2. 3D ビューで `N` キーを押し、サイドバーの **VRoid** タブを開きます。
3. **Malloc's Vroid Blender Tools** パネルで **Bones**、**Mesh**、**Convert**、**Rename** のいずれかを選びます。
4. プレビューとスキップ対象を確認します。
   ボーン名のプレビューは初期状態では折りたたまれています。
   見出しをクリックすると展開できます。
5. タブ内の実行ボタンを押します。

Blender の「元に戻す」（`Ctrl+Z`）に対応しています。
ボーン名を変更しても、階層、レストポーズ、トランスフォームは変わりません。
対応する名前が不明なボーンや、名前が競合するボーンは変更しません。
マテリアル名は意味のある部分の大文字・小文字を保持し、重複する場合は `.001` などの接尾辞が付きます。

### 選択したメッシュの操作

オブジェクトモードで、1 つ以上のメッシュオブジェクトを選択します。

- **Mesh → Separate by Material:** Blender 標準の分離機能で、選択した各メッシュを分離します。
  メッシュ全体を処理し、分離後のパーツを選択状態にします。
  オブジェクト名やマテリアル名は変更しません。
- **Rename → Rename Object and Mesh:** 最初の空でないマテリアルスロットの名前を、オブジェクトとメッシュデータに付けます。
  複数のマテリアルがある場合は、警告を確認してから実行します。
  マテリアルがないメッシュは変更しません。

先に分離してから、選択したパーツの名前をまとめて変更できます。
名前が競合する場合は、Blender が数字の接尾辞を付けます。
共有メッシュデータは、他のオブジェクトを保護するため、必要に応じてシングルユーザー化します。

### マテリアルの基本変換

変換時には Principled BSDF、Material Output、Image Texture ノードを作成します。
法線テクスチャがある場合は、標準の Normal Map ノードも作成します。

| MToon の入力 | Principled への転送先 |
| --- | --- |
| メインテクスチャ | Base Color |
| テクスチャのアルファ | 透過マテリアルの Alpha。不透明マテリアルは不透明のまま |
| 法線テクスチャ | 元の強度を設定した Normal Map ノード |
| 発光テクスチャ | Emission Color。強度は Principled の入力ソケットに設定 |
| 両面表示の設定 | 裏面カリングの設定 |

テクスチャがない場合は、元の色とアルファ値をソケットの初期値に設定します。
テクスチャを接続する場合は、元の色の乗算やアルファの倍率は適用しません。
基本的な入力の転送であり、MToon の見た目を完全に再現するものではありません。
アルファカットオフ、トゥーンシェーディング、リムライト、MatCap、輪郭線、UV アニメーションは転送しません。

マテリアル操作の対象は、選択したアーマチュアにバインドされたメッシュだけで使われているマテリアルです。
無関係なオブジェクトと共有しているマテリアルはスキップします。
変換では、UV 変換、フィルタリング、ラッピングが既定値と異なる場合もスキップします。
スキップする理由はプレビューに表示されます。
変換済みのマテリアルもスキップします。

## ソースからビルド

このリポジトリをクローンするか、**Code → Download ZIP** でダウンロードして展開します。
リポジトリのフォルダで、PowerShell から次のコマンドを実行します。

```powershell
.\build.ps1
```

既定では Steam 版 Blender を使用します。
別の場所にインストールした場合は、実行ファイルを指定します。

```powershell
.\build.ps1 -BlenderPath 'C:\path\to\blender.exe'
```

Blender が `PATH` に登録されていれば、各 OS で次のコマンドを使えます。

```sh
blender --command extension build --source-dir vroid_blender_tools --output-dir .
```

リポジトリのフォルダに `vroid_blender_tools-0.3.0.zip` が作成されます。
上の[インストール手順](#インストール)に従ってインストールしてください。

## ソースを使った開発

ソースの変更を直接反映するには、Blender を閉じてから、`vroid_blender_tools` パッケージフォルダをローカルのエクステンションリポジトリにリンクします。
Windows では、ソースリポジトリのフォルダで次のコマンドを実行します。

```powershell
$source = (Resolve-Path .\vroid_blender_tools).Path
$repository = Join-Path $env:APPDATA 'Blender Foundation\Blender\5.0\extensions\user_default'
New-Item -ItemType Directory -Path $repository -Force | Out-Null
New-Item -ItemType Junction -Path (Join-Path $repository 'vroid_blender_tools') -Target $source
```

使用する Blender のバージョンに合わせてフォルダ名を変更してください。
ジャンクションを作成する前に、インストール済みの同じエクステンションを削除してください。
プリファレンスでローカルのエクステンションを更新し、有効にします。
ソースを変更した後は Blender を再起動してください。

Blender を使わない Python テストは、リポジトリのフォルダから実行できます。

```sh
python -m unittest discover -s tests
```

## ライセンスと依存関係

[MIT](LICENSE)、copyright 2026 malloc。
エクステンション ZIP にはライセンスのコピーが含まれています。

このプロジェクトは Blender の Python API と、別途インストールする [VRM Add-on for Blender](https://github.com/saturday06/VRM-Addon-for-Blender) を使用します。
VRM Add-on は iCyP によって開発され、saturday06 によって保守されています。
これらの依存ソフトウェアは同梱しておらず、ライセンスも変更していません。
テストには合成データを使い、アバターやテクスチャは含めていません。
