from nipype_walker import spm_walker


def walk():
    """

    Inspect NiPype to extract features

    :return: dict
    """
    return spm_walker.walk()


if __name__ == '__main__':
    print(walk())
