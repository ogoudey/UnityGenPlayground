## World Generator

### Installation
```
git clone <git link of this repo>
cd Acrogen

```

### Python Environment

#### Install Dependencies
```
# Make sure you're in /Acrogen
py -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```
Make sure all python requirements are fulfilled. If the next step doesn't work, they are not.

#### Running
Running the generator involves starting up a server.

To start:
```
py -m entry.server
```

To stop:
```
ctrl + C
```

## Unity Project
(From anywhere:)
```
git clone <git link of Unity Special Assets>
./symlink_all.sh Scripts <path_to_a_Unity_project>/Assets
```
Should see a new menu added to the Unity project editor.