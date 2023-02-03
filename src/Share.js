import {
    FacebookShareButton,
    RedditShareButton,
    TwitterShareButton,
  } from "react-share";

  import {
    FacebookIcon,
    RedditIcon,
    TwitterIcon,
} from "react-share";

const Share = ({shareurl}) => {
    return (
        <div>
            <FacebookShareButton url={shareurl} children="FacebookIcon"><FacebookIcon id="FacebookIcon"></FacebookIcon></FacebookShareButton>
            <TwitterShareButton url={shareurl} children="TwitterIcon"><TwitterIcon id="TwitterIcon"></TwitterIcon></TwitterShareButton>
            <RedditShareButton url={shareurl} children="RedditIcon"><RedditIcon id="RedditIcon"></RedditIcon></RedditShareButton>
        </div>
    )
}
export default Share;
