import os
import fire
from alive_progress import alive_bar
from typing import Union
from validator import is_dir, is_extension, is_bool, is_in_range, is_positive_number
from utils import natural_keys, show_info, setup_logger, append_prefix, enumerate_with_step, gen_random_filename, UserResponse, ask


logger = setup_logger(__name__)


class ImageRenamer():
    """Class for renaming images."""

    def __init__(
            self,
            target_dir: str = '',
            digit: int = 4,
            extensions: Union[str, tuple[str]] = None,
            initial_number: int = 1,
            step: int = 1,
            yes: bool = False
    ):
        """Initialize

        Args:
            target_dir (str): Target directory. Defaults to ''.
            digit (int): Number of digits for renaming. Defaults to 4.
            extensions (Union[str, Tuple[str]]): Extensions. Defaults to None.
            initial_number (int): Initial number. Defaults to 1.
            step (int): Step. Defaults to 1.
            yes (bool): Flag for asking to execute or not. Defaults to False.
        """
        self.target_dir: str = target_dir
        self.digit: int = digit
        if not extensions:
            extensions = ('jpg')
        self.extensions: Union[str, tuple[str]] = append_prefix(extensions, ".")
        self.initial_number: int = initial_number
        self.step = step
        self.yes: bool = yes

    def _input_is_valid(self) -> bool:
        """Validator for input.

        Returns:
            bool: True if is valid, False otherwise.
        """
        is_valid = True

        # Check target_dir
        if not is_dir(self.target_dir):
            logger.error(
                'You must type a valid directory for TARGET DIRECTORY. (-t, --target_dir)'
            )
            is_valid = False

        # Check digit
        if not is_in_range(self.digit, 3, 9, False):
            logger.error('You must type a number for DIGIT. [Min: 3, Max: 9] (-d, --digit)')
            is_valid = False

        # Check extensions
        for extension in self.extensions:
            if not is_extension(extension):
                logger.error('You must type at least one EXTENSION. (-e, --extensions)')
                is_valid = False

        # Check initial_number
        if not self.initial_number == 0 and not is_positive_number(self.initial_number):
            logger.error(
                'You must type a ZERO or positive number for INITIAL NUMBER. (-i, --initial_number)'
            )
            is_valid = False

        # Check step
        if not is_positive_number(self.step):
            logger.error(
                'You must type a positive number for STEP. (-s, --step)'
            )
            is_valid = False

        # Check yes
        if not is_bool(self.yes):
            logger.error(
                'You must just type -y flag. No need to type a parameter. (-y, --yes)'
            )
            is_valid = False

        return is_valid

    def rename(self):
        """Rename to sequential number.

        Rename the filename in each directory to sequential number.
        It will rename recursively based on the self.target_dir.
        """
        show_info(self)
        if not self._input_is_valid():
            logger.info('Input parameter is not valid. Try again.')
            return

        total_dirs = sum([len(dirs) for _, dirs, _ in os.walk(self.target_dir)])
        total_dirs_char_len = len(str(total_dirs))
        logger.info(f'{total_dirs} directories will be executed.')

        if not self.yes:
            user_response = ask()
            if user_response == UserResponse.NO:
                logger.info('Abort...')
                return

        logger.info('Start renaming images to sequential number...')

        for i, directory_tree in enumerate(os.walk(self.target_dir)):

            # Unpack directory info
            current_dir, dirs, files = directory_tree

            logger.info(f'Watching {current_dir}.')
            filenames = []
            for filename in sorted(files, key=natural_keys):
                if filename.endswith(self.extensions):
                    path = os.path.join(current_dir, filename)
                    filenames.append(path)

            if not filenames:
                logger.info(
                    f'There are no {", ".join(self.extensions).upper()} files at {current_dir}.'
                )
                continue

            with alive_bar(len(filenames), bar='filling', spinner='dots_waves') as bar:
                for j, filename in enumerate_with_step(filenames, self.initial_number, self.step):
                    _, extension = os.path.splitext(filename)
                    dst_filename = os.path.join(
                        current_dir, f'{j:0{self.digit}}{extension}')

                    # If the file already renamed, skip
                    if filename == dst_filename:
                        bar()
                        continue

                    # If the file already exists at the renamed location, rename the existed file to some random name
                    if os.path.exists(dst_filename):
                        tmp_filename = gen_random_filename(current_dir, extension)
                        try:
                            existed_file_index = filenames.index(dst_filename)
                        except ValueError:
                            logger.error('Existed filename suddenly dissappeared!')
                            logger.error('Unexpected error occurred! Abort...')
                            return

                        filenames[existed_file_index] = tmp_filename
                        os.rename(dst_filename, tmp_filename)

                    os.rename(filename, dst_filename)
                    bar()

            logger.info(
                f'Renamed {", ".join(self.extensions).upper()} files at {current_dir}.'
            )
            logger.info(f'PROGRESS: {i:0{total_dirs_char_len}}/{total_dirs}')

        logger.info('Abort...')


if __name__ == '__main__':
    fire.Fire(ImageRenamer)
