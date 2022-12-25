"""Script to build a csgo language file with custom messages"""
import argparse
import re
import shutil
from pathlib import Path
import platform
import os
import getpass

# detect the platform a user is on and set default the path accordingly
def detectPlatformPath():
    if platform.system() == "Linux":
        print("Linux detected.")
        return Path(f"/home/{getpass.getuser()}/.local/share/Steam/steamapps/common/Counter-Strike Global Offensive")
    elif platform.system() == "Darwin":
        print("MacOS detected.")
        print("Platform detection is not yet implemented for MacOS, please specify the path to your game.")
        exit
        #return Path(f"/home/{getpass.getuser()}/.local/share/Steam/steamapps/common/Counter-Strike Global Offensive")
    else:
        print("Windows detected.")
        return Path("C:\Program Files (x86)\Steam\steamapps\common\Counter-Strike Global Offensive")


def main():

    parser = setup_parser()
    csgo_path, custom_path = parse_args(parser)

    # first retrieve lines to change and language
    print("Reading custom file.")
    with open(custom_path, 'r', encoding='utf-16') as custom_file:
        lines = custom_file.readlines()

    language, custom_lines = parse_lines(lines, debug=False)

    # only non English file need to have all lines in it
    if language != "English":
        # then copy and replace from correct language file
        base_language_path = csgo_path / f"csgo_{language}.txt"
        with open(base_language_path, 'r', encoding='utf-16') as csgo_file:
            lines = csgo_file.readlines()

        _, csgo_lines = parse_lines(lines, debug=False)

        csgo_lines.update(custom_lines)

        # build new file
        new_lines = ['"lang"', '{',
                     f'"Language"\t"{language}"', '"Tokens"', '{']

        for key, value in csgo_lines.items():
            cross_plateform_line = key.split('~')
            # if len > 1 then it is a crossplateform line
            if len(cross_plateform_line) > 1:
                # build correct line by adding plateform infos at the end
                if cross_plateform_line[0].startswith('"[english]'):
                    new_lines.append(f"{cross_plateform_line[0]}\t{value}")
                else:
                    new_lines.append(
                        f"{cross_plateform_line[0]}\t{value}\t{cross_plateform_line[1]}")
            else:
                new_lines.append(f"{key}\t{value}")

        new_lines.append('}\n}\n')

        with open("csgo_custom.txt", 'w', encoding='utf-16') as out_file:
            out_file.write('\n'.join(new_lines))

        # copy file to resource folder
        shutil.copy2("csgo_custom.txt", csgo_path)

    # for English file just copy it directly
    else:
        # copy custom.txt as csgo_custom.txt in csgo\resource
        shutil.copy2("custom.txt", csgo_path / "csgo_custom.txt")
    
    if os.path.exists(f"{csgo_path}/csgo_custom.txt"):
        print("csgo_custom.txt created and placed.")
        print("Be sure to add \"-language custom\" to your launch options!")
    


def parse_lines(lines, debug=False):
    """Parse lines in file.

    Args:
        lines : (list) list of file lines

    Returns:
        language : language of the file
        lines_dict : dict of the lines"""
    lines_dict = {}
    language = "English"
    key = None
    value = None
    last_line_x_plateform = False
    x_plateform = None
    multiline = False
    for idx, line in enumerate(lines):
        # remove whitelines characters at the beggining and at the end
        clean_line = line.lstrip('\t\n ')

        if multiline:
            # verify if multiline ends here
            if clean_line.endswith('"\n'):
                line = line.rstrip('\n')
                multiline = False
            else:
                multiline = True
            # just add value to previous key
            lines_dict[key] += line
            # go to next iteration
            continue

        if clean_line.startswith('"'):
            # count number of quotes in line
            quotes = [pos for pos, char in enumerate(
                clean_line) if char == '"']
            nb_quotes = len(quotes)
            if nb_quotes > 2:
                # if number of quotes is pair, then every quote is closed on same line
                if nb_quotes % 2 == 0:
                    if nb_quotes >= 4:
                        key = clean_line[quotes[0]: quotes[1]+1]
                        # use final quotes because it is possible that there is multiple ones
                        value = clean_line[quotes[2]: quotes[-1]+1]

                        # if previous line was a crossplateform one (only for non-english)
                        if last_line_x_plateform and language != "English":
                            key += '~' + x_plateform
                        last_line_x_plateform = False

                        # find cross plateform tag if it exists
                        x_plateform_pattern = '\[[!]?\$.*?\]'
                        # search only after key end because key can have a cross plateform tag in it
                        # (like "SFUI_Confirm_JoinAnotherGameText[!$X360&&!$PS3]")
                        x_plateform_matches = re.findall(
                            x_plateform_pattern, clean_line[quotes[2]:])
                        # if len > 1, it means line end with by a tag like [$WIN32||$PS3||$X360]
                        if len(x_plateform_matches) == 1:
                            # build a special key because otherwise there is duplicate keys
                            x_plateform = x_plateform_matches[0]
                            key += '~' + x_plateform
                            last_line_x_plateform = True

                        if key == '"Language"':
                            language = value.replace('"', '')
                        else:
                            lines_dict[key] = value
                    multiline = False
                else:
                    multiline = True
                    key = clean_line[quotes[0]: quotes[1]+1]
                    value = clean_line[quotes[2]:]
                    lines_dict[key] = value
            else:
                if debug:
                    print("Nb quotes < 2 :" + clean_line)
        else:
            if debug:
                print("No \" a start : " + clean_line)

    return language, lines_dict


def setup_parser():
    """Setup parser arguments and return it"""
    parser = argparse.ArgumentParser()
    parser.add_argument("--csgo_path", required=False)
    parser.add_argument("--custom_path", required=False)
    return parser


def parse_args(parser):
    """Parse the cli arguments.

    Returns:
        csgo : Path to csgo folder
        custom_path: Path to custom language file"""
    args = parser.parse_args()
    csgo_folder_path = Path(args.csgo_path) if args.csgo_path else detectPlatformPath()
    csgo_resource_path = Path(csgo_folder_path, "csgo", "resource")
    custom_path = Path(args.custom_path if args.custom_path else "./custom.txt")
    return csgo_resource_path, custom_path


if __name__ == "__main__":
    main()