#! /usr/bin/env python

SMARTCARD_INSTALLED = False
try:
    import smartcard
    from smartcard.scard import *
    import smartcard.util

    SMARTCARD_INSTALLED = True
except ImportError:
    print("[readid] no smartcard library installed")


def getId():
    result = None

    if SMARTCARD_INSTALLED:

        hresult, hcontext = SCardEstablishContext(SCARD_SCOPE_USER)

        if hresult == SCARD_S_SUCCESS:

            hresult, readers = SCardListReaders(hcontext, [])

            if len(readers) > 0:

                reader = readers[0]

                hresult, hcard, dwActiveProtocol = SCardConnect(
                        hcontext,
                        reader,
                        SCARD_SHARE_SHARED,
                        SCARD_PROTOCOL_T0 | SCARD_PROTOCOL_T1)

                if hresult == 0:
                    hresult, response = SCardTransmit(hcard, dwActiveProtocol, [0xFF, 0xCA, 0x00, 0x00, 0x00])

                    #print(smartcard.util.toHexString(response))

                    result = smartcard.util.toHexString(response)
            #     else:
            #         print("NO_CARD")
            # else:
            #     print("NO_READER")


            hresult = SCardReleaseContext(hcontext)
            if hresult != SCARD_S_SUCCESS:
                raise Exception('Failed to release context: ' + SCardGetErrorMessage(hresult))
        # else:
        #     print("FAILED")

    return result

if __name__ == "__main__":
    print(getId())
